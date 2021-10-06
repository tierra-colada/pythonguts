import argparse
import ast
import astor
import os


def generate_unique_filename(filenames: list, filename: str) -> str:
    '''
    Generates unique filename by adding `_i` to the name.
    For example: `myfile.cpp` becomes `myfile_1.cpp`.
    :param filenames: list of filenames that resides in the folder
    :param filename: base name for a file
    :return: uniquename - filename with unique name
    '''
    basename, extension = os.path.splitext(filename)
    uniquename = filename
    isunique = True
    i = 0
    while True:
        for name in filenames:
            if name.lower() == uniquename.lower():
                isunique = False
                break
        if isunique:
            return uniquename
        uniquename = basename + '_' + str(i) + extension
        isunique = True
        i += 1


def prepare_filename(destfile: str) -> str:
    '''
    Prepare unique filename.
    :param destfile: file name where it is expected it shoud be
    :return: prepared_filename - full path to the NOT yet created file
    '''
    destdir = os.path.dirname(os.path.abspath(destfile))
    filenames = [f for f in os.listdir(destdir) if os.path.isfile(os.path.join(destdir, f))]
    filename = os.path.basename(destfile)
    uniquename = generate_unique_filename(filenames, filename)
    prepared_filename = os.path.join(destdir, uniquename)
    return prepared_filename


class WalkerSrc(astor.TreeWalk):
    # KEY - func node; VALUE - parent
    found_nodes = dict()

    def pre_body_name(self):
        body = self.cur_node
        for i, child in enumerate(body[:]):
            if isinstance(body[i], ast.FunctionDef):
                self.found_nodes[body[i]] = self.parent
            if isinstance(body[i], ast.ClassDef):
                self.walk(body[i])
        return True

    def reset(self):
        self.found_nodes.clear()


class WalkerDest(astor.TreeWalk):
    # KEY - func node; VALUE - parent
    found_nodes = dict()
    # KEY - dest node; VALUE - src node
    matching_nodes = dict()
    walker_src = WalkerSrc()
    replace_nodes_when_walk = False

    def pre_body_name(self):
        body = self.cur_node
        if not body:
            return True

        for i, child in enumerate(body[:]):
            if isinstance(body[i], ast.FunctionDef):
                node_src, node_dest = self.match_nodes(body[i], self.parent)
                if node_dest and node_src:
                    self.found_nodes[node_dest] = self.parent
                    self.matching_nodes[node_dest] = node_src
                    if self.replace_nodes_when_walk:
                        body[i] = node_src
            if isinstance(body[i], ast.ClassDef):
                self.walk(body[i])
        return True

    def match_nodes(self, node_dest, parent_dest):
        """
        Return two variables if matching nodes were found:
        source node and destination node.
        Otherwise return None and None.
        :param node_dest:
        :param parent_dest:
        :return:
        """
        matching_node_src = None
        matching_node_dest = None
        for node_src in self.walker_src.found_nodes:
            parent_src = self.walker_src.found_nodes[node_src]
            matching_node_src, matching_node_dest = self.match_node(node_src, parent_src, node_dest, parent_dest)
            if matching_node_src and matching_node_dest:
                return matching_node_src, matching_node_dest
        return None, None

    @staticmethod
    def match_node(node_src, parent_src, node_dest, parent_dest):
        """
        Return two variables if matching nodes were found:
        source node and destination node.
        Otherwise return None and None.
        :param node_src:
        :param parent_src:
        :param node_dest:
        :param parent_dest:
        :return:
        """
        if not node_dest or not node_src:
            return None, None
        if type(node_dest) != type(node_src):
            return None, None
        if hasattr(node_dest, 'name') != hasattr(node_src, 'name'):
            return None, None
        if hasattr(node_dest, 'name') and hasattr(node_src, 'name') and \
                node_dest.name != node_src.name:
            return None, None
        if hasattr(node_dest, 'args') != hasattr(node_src, 'args'):
            return None, None
        if hasattr(node_dest, 'args') and hasattr(node_src, 'args') and \
                astor.to_source(node_dest.args) != astor.to_source(node_src.args):
            return None, None
        if not parent_dest or not parent_src:
            return None, None
        if type(parent_dest) != type(parent_src):
            return None, None
        if hasattr(parent_dest, 'name') != hasattr(parent_src, 'name'):
            return None, None
        if hasattr(parent_dest, 'name') and hasattr(parent_src, 'name') and \
                parent_dest.name != parent_src.name:
            return None, None
        if hasattr(parent_dest, 'args') != hasattr(parent_src, 'args'):
            return None, None
        if hasattr(parent_dest, 'args') and hasattr(parent_src, 'args') and \
                astor.to_source(parent_dest.args) != astor.to_source(parent_src.args):
            return None, None
        return node_src, node_dest

    def get_unresolved_src_nodes(self) -> list:
        unresolved_nodes_src = list()
        matching_node_src = None
        matching_node_dest = None
        for node_src in self.walker_src.found_nodes:
            parent_src = self.walker_src.found_nodes[node_src]
            for node_dest in self.found_nodes:
                parent_dest = self.found_nodes[node_dest]
                matching_node_src, matching_node_dest = self.match_node(node_src, parent_src, node_dest, parent_dest)
                if matching_node_src:
                    break
            if not matching_node_src:
                unresolved_nodes_src.append(node_src)
        return unresolved_nodes_src

    def reset(self):
        self.found_nodes.clear()
        self.matching_nodes.clear()
        self.walker_src = WalkerSrc()


def main():
    parser = argparse.ArgumentParser(description=
                                     'Replace python function/method definition in destination file. '
                                     'One source file may contain several functions/methods to replace.')
    parser.add_argument('--src-file', dest='srcfile', action='store',
                        type=type('string'), required=True, default=None,
                        help='file with new functions definitions')
    parser.add_argument('--dest-file', dest='destfile', action='store',
                        type=type('string'), required=True,
                        help='file with old functions definitions')
    parser.add_argument('--oldfile-delete', dest='oldfile_del', action='store_true',
                        help='use this to delete old version of destination file')
    parser.add_argument('--oldfile-keep', dest='oldfile_del', action='store_false',
                        help='use this to keep old version of destination file (default)')
    parser.set_defaults(oldfile_del=False)
    args, unknowncmd = parser.parse_known_args()

    if not os.path.isfile(args.srcfile):
        parser.error(f"specified source file doesn't exist:\n{args.srcfile}")

    if not os.path.isfile(args.destfile):
        parser.error(f"specified destination file doesn't exist:\n{args.destfile}")

    tree_src = astor.parse_file(args.srcfile)
    if not tree_src:
        parser.error(f"unable to load source file:\n{args.srcfile}")

    tree_dest = astor.parse_file(args.destfile)
    if not tree_dest:
        parser.error(f"unable to load destination file:\n{args.destfile}")

    walker_src = WalkerSrc()
    walker_src.walk(tree_src)
    if not walker_src.found_nodes:
        parser.error(f"unable to find any function definition in source file:\n{args.srcfile}\n")

    walker_dest = WalkerDest()
    walker_dest.walker_src = walker_src
    walker_dest.walk(tree_dest) # walk only to check if everything is Ok
    unresolved_nodes_src = walker_dest.get_unresolved_src_nodes()
    if unresolved_nodes_src:
        err_msg = (f"unable to find destination functions matching for the following source functions:\n")
        for n in unresolved_nodes_src:
            err_msg += f"{astor.to_source(n)}\n"
        parser.error(err_msg)

    walker_dest.replace_nodes_when_walk = True
    walker_dest.walk(tree_dest) # now replace nodes when walk

    prepared_filename = prepare_filename(args.destfile)
    with open(prepared_filename, "w") as file:
        file.write(astor.to_source(tree_dest))

    if args.oldfile_del:
        os.remove(args.destfile)
    else:
        filename, file_extension = os.path.splitext(args.destfile)
        prepared_oldfilename = prepare_filename(filename + '_OLD' + file_extension)
        os.rename(args.destfile, prepared_oldfilename)

    os.rename(prepared_filename, args.destfile)


if __name__ == '__main__':
    main()