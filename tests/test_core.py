import tempfile
import unittest
from pathlib import Path
from incidentlab import Store

class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name)/'events.db'
        self.s = Store(self.db)
        self.addCleanup(self.s.close)
    def test_dedupe_and_scope(self):
        a=self.s.record('zeon/dm/a','task1','false-success','evidence')
        self.assertEqual(a,self.s.record('zeon/dm/a','task1','false-success','again'))
        self.assertNotEqual(a,self.s.record('sion/dm/a','task1','false-success','evidence'))
        self.assertEqual(len(self.s.events(a)),2)
    def test_independent_gates(self):
        a=self.s.record('scope','task','failure','source')
        with self.assertRaises(ValueError): self.s.finish(a)
        self.s.attest(a,'original','receipt')
        with self.assertRaises(ValueError): self.s.finish(a)
        for gate in ['red','green','deployment']:
            self.s.attest(a,gate,'receipt-'+gate)
        self.s.finish(a)
        self.assertEqual(self.s.show(a)['status'],'closed')
        with self.assertRaises(ValueError): self.s.attest(a,'green','later')
    def test_invalid_gate(self):
        a=self.s.record('scope','task','failure','source')
        with self.assertRaises(ValueError): self.s.attest(a,'unknown','receipt')
        with self.assertRaises(ValueError): self.s.attest(a,'green','')
        with self.assertRaises(ValueError): self.s.record('','task','failure','source')
    def test_persistence(self):
        a=self.s.record('scope','task','failure','source')
        other=Store(self.db)
        try: self.assertEqual(other.show(a)['task'],'task')
        finally: other.close()
    def test_recurrence_is_new_incident_after_close(self):
        a=self.s.record('scope','task','failure','source')
        for gate in ['original','red','green','deployment']: self.s.attest(a,gate,'receipt')
        self.s.finish(a)
        b=self.s.record('scope','task','failure','recurrence')
        self.assertNotEqual(a,b)

if __name__=='__main__': unittest.main()
