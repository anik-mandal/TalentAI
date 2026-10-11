import sys
sys.path.append('.')
from shared.db import get_supabase

supabase = get_supabase()
result = supabase.table('candidates').select('id, name, status, job_id').execute()

for c in result.data:
    print(c['id'], '|', c['job_id'], '|', c['status'], '|', c['name'])