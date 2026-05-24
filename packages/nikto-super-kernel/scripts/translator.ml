(* Translator — Sector 6: Natural language translation (OCaml).
   Standalone binary called via subprocess from Python.
   Usage: translator.ml <src_lang> <tgt_lang> <text>
   Outputs translated text on stdout. *)

type config = {
  src: string;
  tgt: string;
  text: string;
}

let parse_args () =
  if Array.length Sys.argv < 4 then begin
    Printf.eprintf "Usage: %s <src> <tgt> <text>\n" Sys.argv.(0);
    exit 1
  end else {
    src = Sys.argv.(1);
    tgt = Sys.argv.(2);
    text = Sys.argv.(3);
  }

(* Stub — replace with real ONNX/Transformer inference *)
let translate cfg =
  Printf.sprintf "[%s→%s] %s" cfg.src cfg.tgt cfg.text

let () =
  let cfg = parse_args () in
  print_endline (translate cfg)
