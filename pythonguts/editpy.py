import argparse
import ast
import astor
import os
import warnings


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
    # KEY - func node; # VALUE - parent
    found_nodes = dict()

    def pre_body_name(self):
        body = self.cur_node
        for i, child in enumerate(body[:]):
            if isinstance(body[i], ast.FunctionDef):
                self.found_nodes[body[i]] = self.parent
            if isinstance(body[i], ast.ClassDef):
                self.walk(body[i])
        return True


class WalkerDest(astor.TreeWalk):
    # KEY - func node; # VALUE - parent
    walker_src = WalkerSrc()

    # def __init__(self, walker_src: WalkerSrc):
    #     super().__init__()
    #     self.walker_src = walker_src

    def pre_body_name(self):
        body = self.cur_node
        if not body:
            return True

        for i, child in enumerate(body[:]):
            if isinstance(body[i], ast.FunctionDef):
                node_dest, node_src = self.match_node(body[i], self.parent)
                if node_src:
                    body[i] = node_src
            if isinstance(body[i], ast.ClassDef):
                self.walk(body[i])
        return True

    def match_node(self, node, parent):
        """
        Return two variables if matching nodes were found:
        destination node and source node.
        Otherwise return None.
        :param node: node to compare with source nodes
        :param parent: parent of a given node (may be None)
        :return: (node_dest, node_src) or None
        """
        for node_src in self.walker_src.found_nodes:
            if not node or not node_src:
                continue

            if type(node) != type(node_src):
                continue

            if hasattr(node, 'name') != hasattr(node_src, 'name'):
                continue

            if hasattr(node, 'name') and hasattr(node_src, 'name') and \
                    node.name != node_src.name:
                continue

            if hasattr(node, 'args') != hasattr(node_src, 'args'):
                continue

            if hasattr(node, 'args') and hasattr(node_src, 'args') and \
                    astor.to_source(node.args) != astor.to_source(node_src.args):
                continue

            parent_src = self.walker_src.found_nodes[node_src]
            if not parent or not parent_src:
                continue

            if type(parent) != type(parent_src):
                continue

            if hasattr(parent, 'name') != hasattr(parent_src, 'name'):
                continue

            if hasattr(parent, 'name') and hasattr(parent_src, 'name') and \
                    parent.name != parent_src.name:
                continue

            if hasattr(parent, 'args') != hasattr(parent_src, 'args'):
                continue

            if hasattr(parent, 'args') and hasattr(parent_src, 'args') and \
                    astor.to_source(parent.args) != astor.to_source(parent_src.args):
                continue

            return node, node_src

        return None, None


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

    walker_dest = WalkerDest()
    walker_dest.walker_src = walker_src
    walker_dest.walk(tree_dest)

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