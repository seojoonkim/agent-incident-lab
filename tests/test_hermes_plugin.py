import importlib.util
import unittest
from pathlib import Path

PLUGIN=Path(__file__).parents[1]/'__init__.py'

class State:
    def __init__(self): self.data={}
    def get(self,key,default=None): return self.data.get(key,default)
    def set(self,key,value): self.data[key]=value
class Ctx:
    def __init__(self): self.state=State(); self.hooks={}
    def register_hook(self,name,fn): self.hooks[name]=fn

class PluginTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('incidentlab_hermes',PLUGIN)
        self.mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        self.ctx=Ctx(); self.mod.register(self.ctx)
    def test_registers_hooks(self):
        self.assertEqual(set(self.ctx.hooks),{'api_request_error','post_tool_call','pre_llm_call'})
    def test_api_error_is_deduped_and_redacted(self):
        fn=self.ctx.hooks['api_request_error']
        kw=dict(session_id='sess',task_id='task',provider='custom',model='m',error={'type':'TimeoutError','message':'SECRET raw'},retryable=False,retry_count=1,max_retries=1)
        fn(**kw); fn(**kw)
        rows=self.ctx.state.get('incidents')
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]['count'],2)
        self.assertNotIn('SECRET',str(rows)); self.assertEqual(rows[0]['failure'],'api:TimeoutError:exhausted')
    def test_missing_session_or_retryable_is_not_recorded(self):
        f=self.ctx.hooks['api_request_error']
        f(session_id='',error={'type':'TimeoutError'},retryable=False)
        f(session_id='s',error={'type':'TimeoutError'},retryable=True)
        self.assertEqual(self.ctx.state.get('incidents',[]),[])
    def test_failed_tool_is_recorded_without_args_or_result(self):
        f=self.ctx.hooks['post_tool_call']; f(session_id='s',task_id='t',tool_name='terminal',args={'secret':'x'},result='password=x ERROR',duration_ms=1)
        rows=self.ctx.state.get('incidents'); self.assertEqual(rows[0]['failure'],'tool:terminal:error')
        self.assertNotIn('password',str(rows)); self.assertNotIn('secret',str(rows))
    def test_pre_llm_context_is_scoped_and_bounded(self):
        api=self.ctx.hooks['api_request_error']
        api(session_id='a',task_id='t',error={'type':'TimeoutError'},retryable=False)
        api(session_id='b',task_id='t',error={'type':'Other'},retryable=False)
        out=self.ctx.hooks['pre_llm_call'](session_id='a',user_message='hello')
        self.assertIn('TimeoutError',out['context']); self.assertNotIn('Other',out['context']); self.assertLess(len(out['context']),2000)
    def test_successful_tool_not_recorded(self):
        self.ctx.hooks['post_tool_call'](session_id='s',tool_name='terminal',result='{"exit_code": 0, "output": "ok"}')
        self.assertEqual(self.ctx.state.get('incidents',[]),[])

if __name__=='__main__': unittest.main()
