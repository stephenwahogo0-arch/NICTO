"""R and Julia statistical modeling wrappers for NIKTO Predictive Engine."""
import json
import os
import subprocess
import tempfile
import time


class REngine:
    def __init__(self, r_path="Rscript"):
        self.r_path = r_path
        self._script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..",
                                         "packages", "nikto-super-kernel", "r")
        self._predict_r = os.path.join(self._script_dir, "predict.r")

    def available(self):
        try:
            subprocess.run([self.r_path, "--version"], capture_output=True, timeout=5)
            return os.path.exists(self._predict_r)
        except Exception:
            return False

    def arima_forecast(self, series, steps=10):
        if not self.available():
            return {"error": "R not available", "model": "r_arima"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"series": series, "steps": steps}, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.r_path, self._predict_r, infile],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "r_arima"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "r_arima"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass

    def glm_probability(self, features, outcomes):
        if not self.available():
            return {"error": "R not available", "model": "r_glm"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"features": features, "outcomes": outcomes}, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.r_path, self._predict_r, infile],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "r_glm"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "r_glm"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass

    def bayesian_model(self, series):
        if not self.available():
            return {"error": "R not available", "model": "r_bayesian"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"bayesian_series": series}, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.r_path, self._predict_r, infile],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "r_bayesian"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "r_bayesian"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass


class JuliaEngine:
    def __init__(self, julia_path="julia"):
        self.julia_path = julia_path
        self._script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..",
                                         "packages", "nikto-super-kernel", "julia")
        self._probability_jl = os.path.join(self._script_dir, "probability.jl")

    def available(self):
        try:
            subprocess.run([self.julia_path, "--version"], capture_output=True, timeout=10)
            return os.path.exists(self._probability_jl)
        except Exception:
            return False

    def monte_carlo(self, ratings, n_simulations=100000):
        if not self.available():
            return {"error": "Julia not available", "model": "julia_mc"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"ratings": ratings, "n_simulations": n_simulations}, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.julia_path, self._probability_jl, infile],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "julia_mc"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "julia_mc"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass

    def bayesian_elo(self, team_a_rating, team_b_rating, result, n_samples=1000):
        if not self.available():
            return {"error": "Julia not available", "model": "julia_bayesian_elo"}
        data = {"elo_update": {
            "team_a_rating": team_a_rating,
            "team_b_rating": team_b_rating,
            "result": result,
        }, "n_samples": n_samples}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.julia_path, self._probability_jl, infile],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "julia_bayesian_elo"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "julia_bayesian_elo"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass

    def markov_transition(self, series, n_states=5):
        if not self.available():
            return {"error": "Julia not available", "model": "julia_markov"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"series": series, "n_states": n_states}, f)
            infile = f.name
        try:
            result = subprocess.run(
                [self.julia_path, self._probability_jl, infile],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {"error": result.stderr[:200], "model": "julia_markov"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "model": "julia_markov"}
        finally:
            try:
                os.unlink(infile)
            except Exception:
                pass
