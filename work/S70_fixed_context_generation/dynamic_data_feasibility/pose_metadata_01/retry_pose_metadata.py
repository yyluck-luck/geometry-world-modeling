"""Retry after zero-body TLS failure; original failed source/receipt remain intact."""
import importlib.util
from pathlib import Path
D=Path(__file__).parent
spec=importlib.util.spec_from_file_location('bounded_pose_reader',D/'fetch_pose_metadata.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.D=D/'retry_01';module.D.mkdir()
raise SystemExit(module.main())
