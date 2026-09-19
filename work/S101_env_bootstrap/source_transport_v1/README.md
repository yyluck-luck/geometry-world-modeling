# Remote source transport prepared locally

The `vendor/vmem_snapshot` directory contains only seven audit files. It is not a complete runtime checkout. Uploading it alone cannot support a VMem import.

`vmem_source_only.tar.gz` packages 196 source/config/license files from `work/S20_environment/isolated_vmem_source`. All 196 SHA256 values match the preserved S40 manifest. The archive is 357741 bytes, SHA256 `de001a234e97fdf82f16c2ccdba2caad00c5e8ccda6a637e906c33b47ea3da7b`. Every archived file was read back and hash-checked; all Python files parsed with AST. No model weights, dataset files, credentials, environment files, bytecode or external symlinks are included. No upload or runtime import has occurred.

The nine-package probe is not a complete dependency audit. The actual VMem conditioner imports `kornia` and `open_clip`; other paths import `matplotlib`, `trimesh`, and further dependencies. The import inventory in MANIFEST.json includes optional preprocessing/evaluation modules; do not install every listed name blindly. Test the actual pipeline import and add only its necessary dependencies. The constructor calls pretrained model loaders, so an import test must not instantiate VMemPipeline, CLIPConditioner, or AutoEncoder.

Next: recover SSH, query job584548 and retrieve its receipts, verify/extract this bundle into a fresh remote directory, then run the actual pipeline import with networking/model loading disabled. A complete package-level import result is still not neural inference or scientific validation.
