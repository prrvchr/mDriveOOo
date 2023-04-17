/*
 * _yajl2 backend for ijson
 *
 * Contributed by Rodrigo Tobar <rtobar@icrar.org>
 *
 * ICRAR - International Centre for Radio Astronomy Research
 * (c) UWA - The University of Western Australia, 2016
 * Copyright by UWA (in the framework of the ICRAR)
 */

#include "common.h"
#include "async_reading_generator.h"
#include "basic_parse.h"
#include "basic_parse_async.h"
#include "basic_parse_basecoro.h"
#include "parse.h"
#include "parse_async.h"
#include "parse_basecoro.h"
#include "items.h"
#include "items_async.h"
#include "items_basecoro.h"
#include "kvitems.h"
#include "kvitems_async.h"
#include "kvitems_basecoro.h"

enames_t enames;
PyObject *dot, *item, *dotitem;
PyObject *JSONError;
PyObject *IncompleteJSONError;
PyObject *Decimal;

static PyMethodDef yajl2_methods[] = {
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

PyObject* ijson_return_self(PyObject *self)
{
	Py_INCREF(self);
	return self;
}

PyObject* ijson_return_none(PyObject *self)
{
	Py_RETURN_NONE;
}

/* Module initialization */

/* Support for Python 2/3 */
#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "_yajl2", "wrapper for yajl2 methods", -1, yajl2_methods};
	#define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
	#define MOD_DEF(m, name, doc, methods) \
		m = PyModule_Create(&moduledef);
	#define MOD_VAL(v) v
#else
	#define MOD_INIT(name) PyMODINIT_FUNC init##name(void)
	#define MOD_DEF(m, name, doc, methods) \
		m = Py_InitModule3(name, methods, doc);
	#define MOD_VAL(v)
#endif

#define ADD_TYPE(name, type) \
	{ \
		type.tp_new = PyType_GenericNew; \
		X_LZ(PyType_Ready(&type), MOD_VAL(NULL)); \
		Py_INCREF(&type); \
		PyModule_AddObject(m, name, (PyObject *)&type); \
	}

MOD_INIT(_yajl2)
{
	PyObject *m;
	MOD_DEF(m, "_yajl2", "wrapper for yajl2 methods", yajl2_methods);
	X_N(m, MOD_VAL(NULL));

	ADD_TYPE("basic_parse_basecoro", BasicParseBasecoro_Type);
	ADD_TYPE("basic_parse", BasicParseGen_Type);
	ADD_TYPE("parse_basecoro", ParseBasecoro_Type);
	ADD_TYPE("parse", ParseGen_Type);
	ADD_TYPE("kvitems_basecoro", KVItemsBasecoro_Type);
	ADD_TYPE("kvitems", KVItemsGen_Type);
	ADD_TYPE("items_basecoro", ItemsBasecoro_Type);
	ADD_TYPE("items", ItemsGen_Type);
#if PY_VERSION_HEX >= 0x03050000
	ADD_TYPE("_async_reading_iterator", AsyncReadingGeneratorType);
	ADD_TYPE("basic_parse_async", BasicParseAsync_Type);
	ADD_TYPE("parse_async", ParseAsync_Type);
	ADD_TYPE("kvitems_async", KVItemsAsync_Type);
	ADD_TYPE("items_async", ItemsAsync_Type);
#endif // PY_VERSION_HEX >= 0x03050000

	dot = STRING_FROM_UTF8(".", 1);
	item = STRING_FROM_UTF8("item", 4);
	dotitem = STRING_FROM_UTF8(".item", 5);
#define INIT_ENAME(x) enames.x##_ename = STRING_FROM_UTF8(#x, strlen(#x))
	INIT_ENAME(null);
	INIT_ENAME(boolean);
	INIT_ENAME(integer);
	INIT_ENAME(double);
	INIT_ENAME(number);
	INIT_ENAME(string);
	INIT_ENAME(start_map);
	INIT_ENAME(map_key);
	INIT_ENAME(end_map);
	INIT_ENAME(start_array);
	INIT_ENAME(end_array);

	// Import globally-used names
	PyObject *ijson_common = PyImport_ImportModule("ijson.common");
	PyObject *decimal_module = PyImport_ImportModule("decimal");
	X_N(ijson_common, MOD_VAL(NULL));
	X_N(decimal_module, MOD_VAL(NULL));

	JSONError = PyObject_GetAttrString(ijson_common, "JSONError");
	IncompleteJSONError = PyObject_GetAttrString(ijson_common, "IncompleteJSONError");
	Decimal = PyObject_GetAttrString(decimal_module, "Decimal");
	X_N(JSONError, MOD_VAL(NULL));
	X_N(IncompleteJSONError, MOD_VAL(NULL));
	X_N(Decimal, MOD_VAL(NULL));

	return MOD_VAL(m);

}