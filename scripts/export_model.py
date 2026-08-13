#!/usr/bin/env python
"""Export BGE-small to ONNX so the query path skips the ~17s torch import.

Run once (or after changing MODEL). Verifies parity against sentence-transformers
before declaring success - a silent pooling mismatch would degrade retrieval
invisibly.
"""
from __future__ import print_function
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL = "BAAI/bge-small-en-v1.5"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
PROBE = "pass@5 difficulty gate naive search archetype"


def main():
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    tok = AutoTokenizer.from_pretrained(MODEL)
    mdl = AutoModel.from_pretrained(MODEL).eval()
    tok.save_pretrained(OUT)

    enc = tok(["hello world"], return_tensors="pt", padding=True, truncation=True, max_length=512)
    args = (enc["input_ids"], enc["attention_mask"], enc["token_type_ids"])
    path = os.path.join(OUT, "bge-small.onnx")
    t = time.time()
    torch.onnx.export(
        mdl, args, path,
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["last_hidden_state"],
        dynamic_axes={"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"},
                      "token_type_ids": {0: "b", 1: "s"}, "last_hidden_state": {0: "b", 1: "s"}},
        opset_version=14, do_constant_folding=True)
    print("exported %s  (%.0f MB, %.1fs)" % (path, os.path.getsize(path) / 1e6, time.time() - t))

    # parity: ONNX CLS-pool+normalize must match sentence-transformers exactly
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dr
    dr._ENC[0] = None
    got = dr.encoder()([PROBE])[0]
    from sentence_transformers import SentenceTransformer
    ref = SentenceTransformer(MODEL, device="cpu").encode([PROBE], normalize_embeddings=True)[0]
    cos = float(np.dot(ref, got))
    print("parity cosine(sentence-transformers, onnx) = %.6f" % cos)
    if cos < 0.999:
        print("PARITY BROKEN - pooling mismatch; do not ship this export", file=sys.stderr)
        sys.exit(1)
    print("PARITY OK")


if __name__ == "__main__":
    main()
