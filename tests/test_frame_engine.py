import json
import math
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tgi.frame_engine import FrameEngine
from tgi.identity import encode
from tgi.spatial import LatticeView,SpatialBond,traverse

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=json.loads((ROOT/"contracts/user_acceptance_frame_v1.json").read_text(encoding="utf8"))
A=PACKAGE["experiences"][0]["text"]
B=PACKAGE["experiences"][1]["text"]


def trained():
    engine=FrameEngine()
    for item in PACKAGE["experiences"]:
        engine.ingest(item["text"],item["source_id"])
    return engine


class FrameAcceptanceTests(unittest.TestCase):
    def test_u1_exact_user_acceptance_and_coordinates(self):
        engine=trained()
        for experience,query in zip(PACKAGE["experiences"],PACKAGE["queries"]):
            result=engine.resolve(query["trigger"],query["anchor"])
            self.assertEqual(result.status,"RESOLVED")
            self.assertEqual(result.text,query["expected"])
            self.assertEqual(result.identities,encode(query["expected"]))
            self.assertEqual(result.path[0],tuple(experience["start_coordinate"]))
            self.assertEqual(len(result.path),len(experience["text"]))

    def test_u2_absent_anchor_is_null(self):
        answer=trained().resolve("S",9)
        self.assertEqual(answer.status,"NO_PATH")
        self.assertIsNone(answer.text)
        self.assertEqual(answer.identities,())

    def test_u3_cross_anchor_edges_are_never_followed(self):
        engine=trained(); view=engine.view()
        bonds=dict(view.bonds)
        start=engine.resolve("S",3).path[5]  # M in SISTEM
        foreign=engine.resolve("S",8).path[7]  # R in REAKTOR
        bonds[start]=bonds[start]+(SpatialBond(start,foreign,1e100),)
        altered=LatticeView(view.atoms,bonds,view.origins)
        result=traverse(altered,"S",3)
        self.assertEqual(result.text,A)
        self.assertTrue(all(coord[3:]==(3,5) for coord in result.path))

    def test_u4_repeated_identities_have_distinct_occurrences_and_end(self):
        engine=trained(); result=engine.resolve("S",3); view=engine.view()
        positions=[coord for coord in result.path if view.atoms[coord].identity==encode("S")[0]]
        self.assertGreater(len(positions),1)
        self.assertEqual(len(set(positions)),len(positions))
        self.assertTrue(view.atoms[result.path[-1]].terminal)
        self.assertTrue(all(not view.atoms[c].terminal for c in result.path[:-1]))
        self.assertEqual(engine.resolve("S",3,len(A)).text,A)

    def test_u5_all_chunk_splits_and_no_early_anchor(self):
        for split in range(len(A)+1):
            engine=FrameEngine(); frame=engine.begin("a")
            frame.feed(A[:split]); frame.feed(A[split:])
            self.assertEqual(engine.resolve("S",3).status,"NO_PATH")
            self.assertEqual(engine.commit(frame).anchor,3)
            self.assertEqual(engine.resolve("S",3).text,A)
        first,second=FrameEngine(),FrameEngine()
        fa,fb=first.begin("a"),second.begin("b")
        fa.feed("SISTEM "); fb.feed("SISTEM ")
        self.assertEqual(tuple(e.identity for e in fa.events),tuple(e.identity for e in fb.events))
        self.assertEqual(first.inspect()["anchors"],second.inspect()["anchors"])

    def test_u6_replay_and_new_source_alias_do_not_add_crystal(self):
        engine=trained(); before=engine.inspect()
        engine.ingest(A,"experience-A")
        self.assertEqual(engine.inspect(),before)
        receipt=engine.ingest(A,"another-source")
        self.assertTrue(receipt.reused)
        self.assertEqual(receipt.anchor,3)
        self.assertEqual(engine.inspect()["atoms"],before["atoms"])
        self.assertEqual(engine.inspect()["contexts"],2)

    def test_u7_c_or_l_disconnection_blocks_commit(self):
        for kind in ("C","L"):
            engine=FrameEngine(); frame=engine.begin("a"); frame.feed(A)
            if kind=="C":
                frame._c[0].clear()
            else:
                frame._l=[None]*8
            with self.assertRaises(ValueError):
                engine.commit(frame)
            self.assertEqual(engine.inspect()["atoms"],0)
            self.assertEqual(engine.resolve("S",3).status,"NO_PATH")

    def test_u8_invalid_input_is_atomic(self):
        engine=trained(); before=engine.inspect()
        with self.assertRaises(ValueError):
            engine.ingest("changed","experience-A")
        with self.assertRaises(ValueError):
            engine.ingest("","empty")
        with self.assertRaises(ValueError):
            engine.ingest("valid\ud800","surrogate")
        self.assertEqual(engine.inspect(),before)
        frame=engine.begin("new"); frame.feed("ABC")
        events=frame.events
        with self.assertRaises(ValueError):
            frame.feed("DEF\ud800")
        self.assertEqual(frame.events,events)
        frame.feed("DEF")
        receipt=engine.commit(frame)
        self.assertEqual(engine.resolve("A",receipt.anchor).text,"ABCDEF")

    def test_u9_omega_xi_and_force_match_geometry(self):
        engine=trained(); view=engine.view()
        for atom in view.atoms.values():
            self.assertEqual(atom.omega,Fraction(1))
            self.assertEqual(atom.xi,Fraction(1))
        for edges in view.bonds.values():
            for edge in edges:
                x,y=edge.start,edge.end
                d2=sum((a-b)**2 for a,b in zip(x,y))
                cosine=sum(a*b for a,b in zip(x,y))/math.sqrt(sum(a*a for a in x)*sum(b*b for b in y))
                self.assertGreater(edge.force,0)
                self.assertAlmostEqual(edge.force,cosine/d2,places=14)

    def test_u10_nonfixture_unicode_and_lane_wrap(self):
        engine=FrameEngine()
        samples=["A","SSSSSS","é e\u0301\r\n😀", "\x00X\x00", "任意の文字列", " "]
        samples += ["COMMON PREFIX "+str(i)+" final" for i in range(24)]
        for i,text in enumerate(samples):
            receipt=engine.ingest(text,"source-"+str(i))
            self.assertEqual(engine.resolve(text[0],receipt.anchor).text,text)
        self.assertEqual(engine.inspect()["contexts"],len(samples))

    def test_u11_checkpoint_reload_and_tamper(self):
        engine=trained()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"crystal.json"
            engine.save(path)
            restored=FrameEngine.load(path)
            self.assertEqual(restored.inspect(),engine.inspect())
            for query in PACKAGE["queries"]:
                self.assertEqual(restored.resolve(query["trigger"],query["anchor"]),
                                 engine.resolve(query["trigger"],query["anchor"]))
            obj=json.loads(path.read_text()); obj["payload"]["sources"][0]["text"]+="X"
            path.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):
                FrameEngine.load(path)

    def test_u12_lattice_only_and_bond_disconnection(self):
        engine=trained(); view=engine.view()
        engine._sources.clear(); engine._contexts.clear()
        self.assertEqual(traverse(view,"S",3).text,A)
        bonds=dict(view.bonds); bonds.pop(view.origins[3])
        answer=traverse(LatticeView(view.atoms,bonds,view.origins),"S",3)
        self.assertEqual(answer.status,"INCOMPLETE")
        self.assertIsNone(answer.text)
        atoms=dict(view.atoms)
        first=view.origins[3]; atoms[first]=replace(atoms[first],xi=Fraction(0))
        answer=traverse(LatticeView(atoms,view.bonds,view.origins),"S",3)
        self.assertIsNone(answer.text)

    def test_u13_unknown_trigger_and_safety_ceiling(self):
        engine=trained()
        self.assertIsNone(engine.resolve("X",3).text)
        self.assertIsNone(engine.resolve("S",99).text)
        for limit in (0,1,len(A)-1):
            result=engine.resolve("S",3,limit)
            self.assertEqual(result.status,"INCOMPLETE")
            self.assertIsNone(result.text)
            self.assertEqual(result.identities,())

    def test_u14_long_frame_and_ownership(self):
        text="S"+"AB A😀"*300
        engine=FrameEngine(); frame=engine.begin("long")
        for start in range(0,len(text),17):
            frame.feed(text[start:start+17])
        receipt=engine.commit(frame)
        self.assertEqual(sum(receipt.c_counts),len(text)-1)
        intervals=sorted(receipt.l_ownership,key=lambda item:item[1])
        self.assertEqual(intervals[0][1],0)
        self.assertEqual(intervals[-1][2],len(text))
        for a,b in zip(intervals,intervals[1:]):
            self.assertEqual(a[2],b[1])
        self.assertTrue(any(owner==7 and stop-start>128 for owner,start,stop in intervals))
        self.assertEqual(engine.resolve("S",3).text,text)

    def test_checkpoint_rejects_unfinished_frame(self):
        engine=FrameEngine(); engine.begin("open").feed("S")
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"state.json"
            with self.assertRaises(ValueError):
                engine.save(path)
            self.assertFalse(path.exists())

    def test_abort_preserves_published_state(self):
        engine=trained(); before=engine.inspect()
        frame=engine.begin("aborted"); frame.feed("unfinished")
        engine.abort(frame)
        self.assertEqual(engine.inspect(),before)
        with self.assertRaises(ValueError):
            frame.feed("more")
        with self.assertRaises(ValueError):
            engine.commit(frame)

    def test_cli_complete_acceptance_and_atomic_file_failure(self):
        import subprocess,sys
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)/"state.json"
            def call(*args):
                return subprocess.run([sys.executable,"-m","tgi",*args],cwd=ROOT,capture_output=True,text=True)
            learned=call("ingest","--input",str(ROOT/"examples/acceptance_frames.jsonl"),"--state",str(state))
            self.assertEqual(learned.returncode,0,learned.stderr)
            self.assertEqual(json.loads(learned.stdout)["engine"]["anchors"],[3,8])
            for query in PACKAGE["queries"]:
                run=call("query","--state",str(state),"--trigger",query["trigger"],"--anchor",str(query["anchor"]))
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertEqual(json.loads(run.stdout)["text"],query["expected"])
            inspected=call("inspect","--state",str(state),"--anchor","3")
            self.assertEqual(inspected.returncode,0,inspected.stderr)
            self.assertEqual(len(json.loads(inspected.stdout)["receipts"]),1)
            before=state.read_bytes()
            bad=Path(directory)/"bad.jsonl"
            bad.write_text(json.dumps({"source_id":"new","text":"valid frame"})+"\n{}\n")
            failed=call("ingest","--input",str(bad),"--state",str(state))
            self.assertNotEqual(failed.returncode,0)
            self.assertEqual(state.read_bytes(),before)
