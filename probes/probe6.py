from semantica.reasoning.reasoner import Reasoner
import inspect
print("forward_chain sig:", inspect.signature(Reasoner.forward_chain))
print("add_rule sig:", inspect.signature(Reasoner.add_rule))
print("add_fact sig:", inspect.signature(Reasoner.add_fact))
print("infer_facts sig:", inspect.signature(Reasoner.infer_facts))
from semantica.reasoning.graph_reasoner import GraphReasoner
print("GraphReasoner.reason sig:", inspect.signature(GraphReasoner.reason))
print(inspect.getdoc(GraphReasoner.reason)[:400])
