==================================
Usage
==================================

Installation and requirements
=============================

To install ``capnpy``, just type::

  $ pip install capnpy

``capnpy`` relies on the official capnproto implementation to parse the schema
files, so it needs to be able to find the ``capnp`` executable to compile a
schema.  It requires ``capnp 0.5.0`` or later.


Quick example
=============

Suppose to have a capnp schema called ``example.capnp``::

    @0xe62e66ea90a396da;
    struct Point {
        x @0 :Int64;
        y @1 :Int64;
    }

You can use ``capnpy`` to read and write messages of type ``Point``::

    import capnpy

    # load the schema using dynamic loading
    example = capnpy.load_schema('example')

    # create a new Point object
    p = example.Point(x=1, y=2)

    # serialize the message and load it back
    message = capnpy.dumps(p)
    p2 = capnpy.loads(message)
    print p2.x, p2.y


Loading schemas
================

``capnpy`` supports two different ways of loading schemas:

:dynamic: to compile load capnproto schemas on the fly.
:precompiled: to generate Python bindings for a schema, to be imported
    later.

If you use `dynamic loading`_, you always need the ``capnp`` executable
whenever you want to load a schema.

If you use `precompiled mode`__, you need ``capnp`` to compile the schema, but
not to load it later; this means that you can distribute the precompiled
schemas, and the client machines will be able to load it without having to
install the official capnproto distribution.

.. __: #manual-compilation

Compilation options
--------------------

The ``capnpy`` schema compiler has two modes of compilation:

:py mode: Generate pure Python modules, which can be used either on CPython or
   PyPy: it is optimized to be super fast on PyPy. It produces slow code on
   CPython, but it has the advantage of not requiring ``cython``. This is the
   default on PyPy.
:pyx mode: Generate pyx modules, which are then compiled into native extension
   modules by ``cython`` and ``gcc``. It is optimized for speed on
   CPython. This is the default on CPython, if ``cython`` is available.

Moreover, it supports the following options:

:convert_case: If enabled, ``capnpy`` will automatically convert field names
   from camelCase to underscore_delimiter: i.e., ``fooBar`` will become
   ``foo_bar``. The default is **True**.


Dynamic loading
-----------------

To dynamically load a capnproto schema, use ``capnpy.load_schema``; its full
signature is::

    def load_schema(self,
                    modname=None, importname=None, filename=None,
                    convert_case=True, pyx='auto'):
        ...

``modname``, ``importname`` and ``filename`` corresponds to three different
ways to specify and locate the schema file to load. You need to pass exactly
one of them.

``modname`` (the default) is interpreted as if it were the name of a Python
module with the ``.capnp`` extension. This means that it is searched in all
the directories listed in ``sys.path`` and that you can use dotted names to
load a schema inside packages or subpackages::

    >>> import capnpy
    >>> import mypackage
    >>> mypackage
    <module 'mypackage' from '/tmp/mypackage/__init__.pyc'>
    >>> example = capnpy.load_schema('mypackage.mysub.example')
    >>> example
    <module 'example' from '/tmp/mypackage/mysub/example.capnp'>

This is handy because it allows you to distribute the capnproto schemas along
the Python packages, and to load them with no need to care where they are on
the filesystem, as long as the package is importable by Python.

``importname`` is similar to ``modname``, with the difference that it uses the
same syntax you would use in capnproto's *import expressions*. In particular,
if you use an absolute path, ``load_schema`` searches for the file in each of
the search path directories, which by default correspond to the ones listed in
``sys.path``. Thus, the example above is completely equivalent to this::

    >>> example = capnpy.load_schema(importname='/mypackage/mysub/example.capnp')
    >>> example
    <module 'example' from '/tmp/mypackage/mysub/example.capnp'>

Finally, ``filename`` specifies the exact file name of the schema file. No
search will be performed.

``pyx`` and ``convert_case`` specify which `compilation options`_ to use.


Manual compilation
-------------------

You can manually compile a capnproto schema by using ``python -m capnpy
compile``::

    $ python -m capnpy compile example.capnp

This will produce ``example.py`` (if you are using py mode) or ``example.so``
(if you are using pyx mode).


Integration with ``setuptools``
--------------------------------

If you use ``setuptools``, you can use the ``capnpy_schema`` keyword to
automatically compile your schemas from ``setup.py``::

    from setuptools import setup
    setup(name='foo',
          version='0.1',
          packages=['mypkg'],
          capnpy_schemas=['mypkg/example.capnp'],
          )


You can specify additional options by using ``capnpy_options``::

    from setuptools import setup
    setup(name='foo',
          version='0.1',
          packages=['mypkg'],
          capnpy_options={
              'pyx': False,          # do NOT use Cython (default is 'auto')
              'convert_case': False, # do NOT convert camelCase to camel_case
                                     # (default is True)
          }
          capnpy_schemas=['mypkg/example.capnp'],
          )



Loading a dumping messages
=============================

The API to read and write capnproto messages is inspired by the ones offered
by ``pickle`` and ``json``:

  - ``capnpy.load(f, payload_type)``: load a message from a file-like object

  - ``capnpy.loads(s, payload)``: load a message from a string

  - ``capnpy.load_all(f, payload_type)``: return a generator which yields all
    the messages from the given file-like object

  - ``capnpy.dump(obj)``: write a message to a file-like object

  - ``capnpy.dumps(obj)``: write a message to a string

For example::

    >>> import capnpy
    >>> example = capnpy.load_schema('example')
    >>> p = example.Point(x=100, y=200)
    >>> mybuf = capnpy.dumps(p)
    >>> mybuf
    '\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00d\x00\x00\x00\x00\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x00\x00'
    >>> p2 = capnpy.loads(mybuf, example.Point)
    >>> print p2.x, p2.y
    100 200

Alternatively, you can call ``load``/``loads`` directly on the class, and
``dump``/``dumps`` directly on the objects::

    >>> import capnpy
    >>> example = capnpy.load_schema('example')
    >>> p = example.Point(x=100, y=200)
    >>> mybuf = p.dumps()
    >>> mybuf
    '\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00d\x00\x00\x00\x00\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x00\x00'
    >>> p2 = example.Point.loads(mybuf)
    >>> print p2.x, p2.y
    100 200


capnproto types
================

Struct
-------

``capnpy`` turns each capnproto struct into a Python class. The API is
inspired by ``namedtuples``:

  - the fields of the struct are exposed as plain attributes

  - objects are **immutable**; it is not possible to change the value of a
    field once the object has been instantiated. If you need to change the
    value of a field, you can instantiate a new object, as you would do with
    namedtuples

  - objects can be made `comparable and hashable`__ by specifying the
    ``$Py.key`` annotation

.. __: #equality-and-hashing


Enum
-----

capnproto enums are represented as subclasses of ``int``, so that we can
easily use both the numeric and the symbolic values::

    enum Color {
        red @0;
        green @1;
        blue @2;
        yellow @3;
    }

::

    >>> example = capnpy.load_schema('example')
    >>> Color = example.Color
    >>> Color.green
    <Color.green: 1>
    >>> int(Color.green)
    1
    >>> str(Color.green)
    'green'
    >>> Color.green + 2
    3
    >>> Color(2)
    <Color.blue: 2>
    >>> Color.__members__
    ('red', 'green', 'blue', 'yellow')


Union
------

capnproto uses a special enum value, called *tag*, to identify the field which
is currently set inside an union; ``capnpy`` follows this semantics by
automatically creating an enum whose members correspond to fields of the
union::

    struct Shape {
      area @0 :Float64;

      union {
        circle @1 :Float64;      # radius
        square @2 :Float64;      # width
      }
    }

::

    >>> example = capnpy.load_schema('example')
    >>> Shape = example.Shape
    >>> Shape.__tag__
    <class 'capnpy.enum.Shape.__tag__'>
    >>> Shape.__tag__.__members__
    ('circle', 'square')

You can query which field is set by calling ``which()``, or by calling one of
the ``is_*()`` methods which are automatically generated::

    >>> s = capnpy.load(f, Shape)
    >>> s.which()
    <Shape.__tag__.circle: 0>
    >>> s.__which__()
    0
    >>> s.is_circle()
    True
    >>> s.is_square()
    False

The difference between ``which()`` and ``__which__()`` is that the former
return an ``Enum`` value, while the latter a raw integer: on CPython,
``which()`` is approximately 2x slower, so you might consider to use the raw
form in performance-critical parts of your code. On PyPy, the two forms have
the very same performance.

Since ``capnpy`` objects are immutable, union fields must be set when
instantiating the object. The first way is to call the default constructor and
set the field as usual::

    >>> s = Shape(area=16, square=4)
    >>> s.is_square()
    True

If you try to specify two conflicting fields, you get an error::

    >>> Shape(area=16, square=4, circle=5)
    Traceback (most recent call last):
    ...
    TypeError: got multiple values for the union tag: circle, square

The second way is to use one of the special ``new_*()`` alternate
constructors::

    >>> s = Shape.new_square(area=16, square=4)
    >>> s.is_square()
    True

    >>> s = Shape.new_square(area=16, square=4, circle=5)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: new_square() got an unexpected keyword argument 'circle'

The alternate constructors are especially handy in case of ``Void`` union
fields, because in that case you don't need to specify the (void) value of the
field::

    struct Type {
      union {
        void @0 :Void;
        bool @1 :Void;
        int64 @2 :Void;
        float64 @3 :Void;
        text @4 :Void;
      }
    }

::

    >>> t = Type.new_int64()
    >>> t.which()
    <Type.__tag__.int64: 2>
    >>> t.is_int64()
    True


Groups
------

Group fields are accessed using the usual dot notation::

    struct Point {
        position :group {
            x @0 :Int64;
            y @1 :Int64;
        }
        color @2 :Text;
    }

::

    >>> p = capnpy.load(f, Point)
    >>> p.position.x
    1
    >>> p.position.y
    2

When creating new objects, group fields are initialized using a tuple::

    >>> p2 = Point(position=(3, 4), 'red')
    >>> p2.position.x
    3
    >>> p2.position.y
    4

It is also possible to construct the tuple using keyword arguments, by using
an helper::

    >>> p3 = Point(position=Point.Position(x=5, y=6), color='red')
    >>> p3.position.x
    5
    >>> p3.position.y
    6

Note the difference between the lowercase ``Point.position`` which is used to
access the field, and the capitalized ``Point.Position`` which is used to
construct new objects.


Named unions
-------------

Named unions are a special case of groups. Suppose to have the following schema::

    @0xbf5147cbbecf40c1;
    struct Person {
      name @0 :Text;
      job :union {
          unemployed @1 :Void;
          retired @2 :Void;
          worker @3 :Text;
      }
    }

You can instantiate new objects as you would do with a normal group. If you
want to specify a ``void`` union field, you can use ``None``::

    >>> example = capnpy.load_schema('example')
    >>> p1 = example.Person(name='John', job=example.Person.Job(retired=None))
    >>> p2 = example.Person(name='John', job=example.Person.Job(worker='capnpy'))

Reading named unions is the same as anonymous ones::

    >>> p1.job.which()
    <job.__tag__.retired: 1>
    >>> p1.job.is_retired()
    True
    >>> p2.job.worker
    'capnpy'


Equality and hashing
====================

By default, structs are not hashable and cannot be compared. To enable, you
need to specify which fields to consider using the ``$Py.key`` annotation::

    using Py = import "/capnpy/annotate.capnp";

    # ignore the name when comparing
    struct Point $Py.key("x, y") {
        x @0 :Int64;
        y @1 :Int64;
        name @2 :Text;
    }

::

    >>> p1 = Point(1, 2, "p1")
    >>> p2 = Point(1, 2, "p2")
    >>> p3 = Point(3, 4, "p3")
    >>>
    >>> p1 == p2
    True
    >>> p1 == p3
    False

If you have many fields, you can use ``$Py.key("*")`` to include all of them
in the comparison key: this is equivalent of explicitly listing all the fields
which are present in the schema. In particular, be aware that if later get
objects which come from a **newer** schema, the additional fields will **not**
be considered in the comparisons.

Moreover, the structs are guaranteed to compare equal to the corresponding
tuples:

    >>> p1 == (1, 2)
    True
    >>> p3 == (3, 4)
    True

Finally, it is possible to use them as dicionary keys::

    >>> d = {}
    >>> d[p1] = 'foo'
    >>> d[p2]
    'foo'
    >>> d[(1, 2)]
    'foo'


**Rationale**: you have to manually specify the fields to consider because it
is not obvious what is the right thing to do in presence of schema
evolution. For example, suppose you start with a ``struct Point`` which
contains only ``x`` and ``y``::

    >>> p1 = Point(1, 2) # there is no "name" yet

Then, you receive some other object created with a newer schema, which
contains also the ``name`` field::

    >>> p2 = Point.load(mysocket)
    >>> p2.x, p2.y
    (1, 2)
    >>> hasattr(p2, 'name')
    False
    >>> p2._buf.s
    '\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x82\x00\x00\x00this is my name\x00'

Note that the underyling data contains the name, although we don't have the
``name`` field (because we used an older schema). So, what should ``p1 == p2``
return? We might choose to simply ignore the name and return ``True``. Or
choose to consider ``p1.name`` equal to the empty string, or to ``None``, and
thus return ``False``. Or we could declare that two objects are equal when
their canonical representation is the same, which introduces even more subtle
consequences.

According to the Zen of Python:

    Explicit is better than implicit.
    In the face of ambiguity, refuse the temptation to guess.

Hence, we require you to explicity specify which fields to consider.


Extending ``capnpy`` structs
=============================

As described above, each capnproto Struct is converted into a Python class,
whose attributes are specified by the capnproto schema. Moreover, with
``capnpy`` you can easily add methods to such classes.

To add methods, use the ``__extend__`` class decorator as shown here::

    >>> import math
    >>> import capnpy
    >>> example = capnpy.load_schema('example')
    >>> p = example.Point(x=3, y=4)
    >>> print p.distance()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'Point' object has no attribute 'distance'
    >>>
    >>> @example.Point.__extend__
    ... class Point:
    ...     def distance(self):
    ...         return math.sqrt(self.x**2 + self.y**2)
    ...
    >>> print p.distance()
    5.0

Although it seems magical, ``__extend__`` is much simpler than it looks: what
it does is simply to copy the content of the new class body ``Point`` into the
body of the automatically-generated ``example.Point``; the result is that
``example.Point`` contains both the original fields and the new methods; as
shown above, this affects also the objects created before the call to
``__extend__``.

When loading a schema, e.g. ``example.capnp``, ``capnpy`` also searches for a
file named ``example_extended.py`` in the same directory. If it exists, the
code is executed in the same namespace as the schema being loaded, meaning
that it is the perfect place where to put the ``__extend__`` code to be sure
that it will be immediately available. For example, suppose to have the
following ``example_extended.py`` in the same directory as ``example.capnp``::

    # example_extended.py
    import math
    @Point.__extend__
    class Point:
        def distance(self):
            return math.sqrt(self.x**2 + self.y**2)

Then, the ``distance`` method will be immediately available as soon as we load
the schema::

    >>> import capnpy
    >>> example = capnpy.load_schema('example')
    >>> p = example.Point(3, 4)
    >>> print p.distance()
    5.0


``capnpy`` vs ``pycapnp``
==========================

XXX write me