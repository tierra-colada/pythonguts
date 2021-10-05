# pythonguts
If your project depends on some external python projects and 
you want to make some changes in external functions/methods 
and then copy/paste these changes automatically - this package may help you. 

There is a tool `editpy` wich we will discuss.

## The idea behind `editpy` tool
`editpy` uses `astor` to find replaceable functions and replaces matching functions.

<ins>To find common function `editpy` checks:</ins>
* are they both _functions?_
* do they both have the same name?
* do they both have the same args?
* do they both have the same parent (i.e. classname for example)?

## Example
original function/method definition file **dest.py**:
 ```python
class MyClass:
    def my_method(self, i: float, j: int, k: float) -> float:
        return 0


def foo(i: float) -> float:
    return i


def bar():
    return 0


# this function stays unchanged
def unchanged():
    return 0
```

new function/method definition file **src.py**:
```python
class MyClass:
    def my_method(self, i: float, j: int, k: float) -> float:
        print('new definition')
        return 0


def foo(i: float) -> float:
    print('new definition')
    return i


def bar():
    print('new definition')
    return 0
```
Run: 

`editpy --src-file=src.py --dest-file=dest.py --oldfile-keep`

`--oldfile-keep` (default) is used to keep the original file (it will be renamed by adding `_OLD_N` suffix). Otherwise use `--oldfile-delete` to delete the original file.

Another option is to run the test (though the test deletes all the generated files so you better take a look in `/tests` dir):

`python -m unittest pythonguts.tests.test_pythonguts`