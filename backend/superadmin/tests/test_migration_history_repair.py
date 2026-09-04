from unittest import TestCase

from superadmin.services.migration_history_repair import missing_ancestors


class _Node:
    def __init__(self, key):
        self.key = key
        self.parents = set()


class _Graph:
    def __init__(self, edges: list[tuple[tuple[str, str], tuple[str, str]]]):
        self.node_map = {}
        for child, parent in edges:
            self.node_map.setdefault(child, _Node(child))
            self.node_map.setdefault(parent, _Node(parent))
            self.node_map[child].parents.add(self.node_map[parent])

    def leaf_nodes(self):
        return list(self.node_map.keys())

    def forwards_plan(self, leaf):
        ordered = []

        def walk(key):
            node = self.node_map[key]
            for parent in node.parents:
                walk(parent.key)
            if key not in ordered:
                ordered.append(key)

        walk(leaf)
        return ordered


class MissingAncestorsTest(TestCase):
    def test_marca_auth_0004_quando_0005_esta_aplicada(self):
        a4 = ("auth", "0004_alter_user_username_opts")
        a5 = ("auth", "0005_alter_user_last_login_null")
        a1 = ("auth", "0001_initial")
        graph = _Graph([(a4, a1), (a5, a4)])
        missing = missing_ancestors(graph, {a1, a5})
        self.assertEqual(missing, [a4])

    def test_nao_marca_nada_se_historico_completo(self):
        a4 = ("auth", "0004_alter_user_username_opts")
        a5 = ("auth", "0005_alter_user_last_login_null")
        a1 = ("auth", "0001_initial")
        graph = _Graph([(a4, a1), (a5, a4)])
        self.assertEqual(missing_ancestors(graph, {a1, a4, a5}), [])
