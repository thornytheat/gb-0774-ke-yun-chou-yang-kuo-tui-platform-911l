from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1] / 'sample_data'
PORT = 18473
MAX_BYTES = 350_000
CHOICES = {'direct': '直达', 'transfer': '换乘', 'other': '其他'}
