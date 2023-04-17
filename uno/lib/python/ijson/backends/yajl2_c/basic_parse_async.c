/*
 * basic_parse_async asynchronous iterable implementation for ijson's C backend
 *
 * Contributed by Rodrigo Tobar <rtobar@icrar.org>
 *
 * ICRAR - International Centre for Radio Astronomy Research
 * (c) UWA - The University of Western Australia, 2020
 * Copyright by UWA (in the framework of the ICRAR)
 */


#include "async_reading_generator.h"
#include "basic_parse_basecoro.h"
#include "common.h"
#include "coro_utils.h"

#if PY_VERSION_HEX >= 0x03050000
/**
 * basic_parse_async asynchronous iterable object structure
 */
typedef struct {
	PyObject_HEAD
	async_reading_generator *reading_generator;
} BasicParseAsync;

/*
 * __init__, destructor and __anext__
 */
static int basicparseasync_init(BasicParseAsync *self, PyObject *args, PyObject *kwargs)
{
	pipeline_node coro_pipeline[] = {
		{&BasicParseBasecoro_Type, NULL, kwargs},
		{NULL}
	};
	M1_N(self->reading_generator = (async_reading_generator *)PyObject_CallObject((PyObject *)&AsyncReadingGeneratorType, args));
	async_reading_generator_add_coro(self->reading_generator, coro_pipeline);
	return 0;
}

static void basicparseasync_dealloc(BasicParseAsync *self) {
	Py_XDECREF(self->reading_generator);
	Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *basicparseasync_anext(PyObject *self)
{
	BasicParseAsync *gen = (BasicParseAsync *)self;
	Py_INCREF(gen->reading_generator);
	return (PyObject *)gen->reading_generator;
}

static PyAsyncMethods basicparseasync_methods = {
	.am_await = ijson_return_self,
	.am_aiter = ijson_return_self,
	.am_anext = basicparseasync_anext
};

PyTypeObject BasicParseAsync_Type = {
#if PY_MAJOR_VERSION >= 3
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	PyObject_HEAD_INIT(NULL)
#endif
	.tp_basicsize = sizeof(BasicParseAsync),
	.tp_name = "_yajl2.basic_parse_async",
	.tp_doc = "Asynchronous iterable yielding (evt,value) tuples",
	.tp_init = (initproc)basicparseasync_init,
	.tp_dealloc = (destructor)basicparseasync_dealloc,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_as_async = &basicparseasync_methods
};

#endif // PY_VERSION_HEX >= 0x03050000