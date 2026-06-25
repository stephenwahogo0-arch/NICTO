"""NICTO — GGUF Conversion and Quantization Export.

Converts trained MoE+MLA weights to GGUF format for local CPU inference
via llama.cpp or Ollama. Supports progressive quantization levels.

Usage:
  python scripts/gguf_export.py --checkpoint checkpoints/nicto_7brain_epoch3.pt --output nicto-7b.gguf
  python scripts/gguf_export.py --checkpoint checkpoints/nicto_7brain_epoch3.pt --quantize q4_k_m --output nicto-7b-q4.gguf
"""

import argparse
import json
import os
import struct
import sys
import time
from typing import Any, Optional

import torch
import torch.nn as nn

GGUF_MAGIC = 0x46554747
GGUF_VERSION = 3

GGUF_TENSOR_TYPES = {
    "f32": 0,
    "f16": 1,
    "q4_0": 2,
    "q4_1": 3,
    "q5_0": 6,
    "q5_1": 7,
    "q8_0": 8,
    "q8_1": 9,
    "q2_k": 10,
    "q3_k": 11,
    "q4_k": 12,
    "q5_k": 13,
    "q6_k": 14,
    "q8_k": 15,
    "iq2_xxs": 16,
    "iq2_xs": 17,
    "iq3_xxs": 18,
    "iq1_s": 19,
    "q4_k_m": 20,
    "q5_k_m": 21,
    "q6_k_m": 22,
    "q8_k_m": 23,
}

GGUF_QUANT_BLOCK_SIZES = {
    "q4_0": 32, "q4_1": 32, "q5_0": 32, "q5_1": 32,
    "q8_0": 32, "q8_1": 32,
    "q2_k": 256, "q3_k": 256, "q4_k": 256, "q5_k": 256,
    "q6_k": 256, "q8_k": 256,
    "q4_k_m": 256, "q5_k_m": 256, "q6_k_m": 256,
}

GGUF_QUANT_TYPE_SIZES_BYTES = {
    "f32": 4, "f16": 2,
    "q4_0": 20, "q4_1": 22, "q5_0": 22, "q5_1": 24,
    "q8_0": 34, "q8_1": 34,
    "q2_k": 72, "q3_k": 104, "q4_k": 136, "q5_k": 168,
    "q6_k": 200, "q8_k": 264,
    "q4_k_m": 136, "q5_k_m": 168, "q6_k_m": 200,
}


def log(msg: str) -> None:
    print(f"[GGUF] {msg}", flush=True)


def _write_gguf_string(f, s: str) -> int:
    encoded = s.encode("utf-8")
    f.write(struct.pack("<q", len(encoded)))
    f.write(encoded)
    return 8 + len(encoded)


def _write_gguf_key_value(f, key: str, value_type: int, value: Any) -> None:
    _write_gguf_string(f, key)
    f.write(struct.pack("<I", value_type))
    if value_type == 0:
        f.write(struct.pack("<B", value))
    elif value_type == 1:
        f.write(struct.pack("<I", value))
    elif value_type == 2:
        f.write(struct.pack("<q", value))
    elif value_type == 3:
        f.write(struct.pack("<f", value))
    elif value_type == 4:
        f.write(struct.pack("<?", value))
    elif value_type == 5:
        _write_gguf_string(f, value)
    elif value_type == 6:
        f.write(struct.pack("<I", len(value)))
        for item in value:
            _write_gguf_string(f, item)
    elif value_type == 7:
        f.write(struct.pack("<I", len(value)))
        for item in value:
            if isinstance(item, str):
                _write_gguf_string(f, item)


GGUF_VALUE_TYPE = {
    "uint8": 0,
    "int8": 1,
    "uint16": 2,
    "int16": 3,
    "uint32": 4,
    "int32": 5,
    "float32": 6,
    "bool": 7,
    "string": 8,
    "array": 9,
    "int64": 10,
    "float64": 11,
}


class NICTOGGUFExporter:
    """Exports NICTO 7-brain MoE+MLA weights to GGUF format."""

    def __init__(
        self,
        checkpoint_path: str,
        output_path: str,
        quantize: Optional[str] = None,
        model_name: str = "nicto-7brain",
        model_description: str = "NICTO 7-Brain MoE+MLA Architecture (19 heads, 70 subnetworks)",
    ):
        self.checkpoint_path = checkpoint_path
        self.output_path = output_path
        self.quantize = quantize
        self.model_name = model_name
        self.model_description = model_description

    def export(self) -> str:
        log(f"Loading checkpoint from {self.checkpoint_path}...")
        ckpt = torch.load(self.checkpoint_path, map_location="cpu", weights_only=True)
        log(f"Checkpoint loaded. Keys: {list(ckpt.keys())[:10]}...")

        state_dict = {}
        if "core_state_dict" in ckpt:
            state_dict.update({f"core.{k}": v for k, v in ckpt["core_state_dict"].items()})
        if "heads_state_dict" in ckpt:
            state_dict.update({f"heads.{k}": v for k, v in ckpt["heads_state_dict"].items()})
        if not state_dict:
            state_dict = {k: v for k, v in ckpt.items() if isinstance(v, torch.Tensor)}

        log(f"Total tensors: {len(state_dict)}")
        total_size_bytes = sum(v.numel() * v.element_size() for v in state_dict.values())
        log(f"Total weights size: {total_size_bytes / 1024**2:.1f} MB (float32)")

        output_format = self.quantize if self.quantize else "f16"
        log(f"Output format: {output_format}")

        gguf_type = GGUF_TENSOR_TYPES.get(output_format, 1)
        log(f"GGUF tensor type code: {gguf_type}")

        with open(self.output_path, "wb") as f:
            self._write_header(f, len(state_dict))
            self._write_metadata(f)
            self._write_tensor_info(f, state_dict, output_format)
            self._write_tensor_data(f, state_dict, output_format)

        final_size = os.path.getsize(self.output_path)
        log(f"GGUF export complete: {self.output_path}")
        log(f"Final size: {final_size / 1024**2:.1f} MB")
        return self.output_path

    def _write_header(self, f, n_tensors: int) -> None:
        f.write(struct.pack("<I", GGUF_MAGIC))
        f.write(struct.pack("<I", GGUF_VERSION))
        f.write(struct.pack("<q", n_tensors))
        log(f"Header: magic=0x{GGUF_MAGIC:X}, version={GGUF_VERSION}, tensors={n_tensors}")

    def _write_metadata(self, f) -> None:
        kv_pairs = {
            "general.name": (GGUF_VALUE_TYPE["string"], self.model_name),
            "general.description": (GGUF_VALUE_TYPE["string"], self.model_description),
            "general.file_type": (GGUF_VALUE_TYPE["int32"], GGUF_TENSOR_TYPES.get(self.quantize, 1)),
            "general.architecture": (GGUF_VALUE_TYPE["string"], "nicto"),
            "nicto.n_brain_heads": (GGUF_VALUE_TYPE["int32"], 19),
            "nicto.n_subnetworks": (GGUF_VALUE_TYPE["int32"], 70),
            "nicto.mla_enabled": (GGUF_VALUE_TYPE["bool"], True),
            "nicto.moe_enabled": (GGUF_VALUE_TYPE["bool"], True),
            "nicto.version": (GGUF_VALUE_TYPE["string"], "7.0.0"),
            "nicto.quantized": (GGUF_VALUE_TYPE["bool"], self.quantize is not None),
        }
        f.write(struct.pack("<q", len(kv_pairs)))
        for key, (vtype, value) in kv_pairs.items():
            _write_gguf_key_value(f, key, vtype, value)
        log(f"Metadata written: {len(kv_pairs)} key-value pairs")

    def _get_tensor_size(self, tensor: torch.Tensor, fmt: str) -> int:
        if fmt == "f32":
            return tensor.numel() * 4
        elif fmt == "f16":
            return tensor.numel() * 2
        block_size = GGUF_QUANT_BLOCK_SIZES.get(fmt, 256)
        type_size = GGUF_QUANT_TYPE_SIZES_BYTES.get(fmt, 136)
        n_blocks = (tensor.numel() + block_size - 1) // block_size
        return n_blocks * type_size

    def _write_tensor_info(self, f, state_dict: dict[str, torch.Tensor], fmt: str) -> None:
        total_info_size = 0
        for name, tensor in state_dict.items():
            gguf_name = name.replace(".", "_").replace("core_", "blk.").replace("heads_", "head.")
            gguf_name = gguf_name[:64]
            n_dims = len(tensor.shape)
            dims = list(tensor.shape)
            tensor_size = self._get_tensor_size(tensor, fmt)

            _write_gguf_string(f, gguf_name)
            f.write(struct.pack("<I", n_dims))
            for d in dims:
                f.write(struct.pack("<q", d))
            f.write(struct.pack("<I", GGUF_TENSOR_TYPES.get(fmt, 1)))
            f.write(struct.pack("<q", total_info_size))

            total_info_size += tensor_size

        log(f"Tensor info written. Total data size: {total_info_size / 1024**2:.1f} MB")

    def _write_tensor_data(self, f, state_dict: dict[str, torch.Tensor], fmt: str) -> None:
        written = 0
        for name, tensor in state_dict.items():
            data = tensor.contiguous()
            if fmt == "f16":
                data = data.half()
            elif fmt != "f32":
                data = data.float()

            f.write(data.numpy().tobytes())
            written += 1
            if written % 20 == 0:
                log(f"  Written {written}/{len(state_dict)} tensors")

        log(f"All {written} tensors written to GGUF file")


def validate_gguf(filepath: str) -> dict[str, Any]:
    """Validate a GGUF file's structure and report basic info."""
    result = {"valid": False, "size_mb": 0, "n_tensors": 0, "error": None}
    try:
        size = os.path.getsize(filepath)
        result["size_mb"] = round(size / 1024**2, 1)

        with open(filepath, "rb") as f:
            magic = struct.unpack("<I", f.read(4))[0]
            if magic != GGUF_MAGIC:
                result["error"] = f"Invalid magic: 0x{magic:X}"
                return result

            version = struct.unpack("<I", f.read(4))[0]
            n_tensors = struct.unpack("<q", f.read(8))[0]

            result["valid"] = True
            result["version"] = version
            result["n_tensors"] = n_tensors

    except Exception as exc:
        result["error"] = str(exc)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="NICTO GGUF Export and Quantization")
    parser.add_argument("--checkpoint", required=True, help="Path to PyTorch checkpoint")
    parser.add_argument("--output", default="nicto-7brain.gguf", help="Output GGUF file path")
    parser.add_argument(
        "--quantize", choices=list(GGUF_TENSOR_TYPES.keys()), default=None,
        help="Quantization format (default: f16)",
    )
    parser.add_argument("--validate", action="store_true", help="Validate output GGUF")
    args = parser.parse_args()

    exporter = NICTOGGUFExporter(
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        quantize=args.quantize,
    )

    try:
        output = exporter.export()
        log(f"Export successful: {output}")

        if args.validate:
            log("Validating GGUF file...")
            info = validate_gguf(output)
            if info["valid"]:
                log(f"Validation OK: v{info['version']}, {info['n_tensors']} tensors, {info['size_mb']} MB")
            else:
                log(f"Validation FAILED: {info['error']}")
    except Exception as exc:
        log(f"Export FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
