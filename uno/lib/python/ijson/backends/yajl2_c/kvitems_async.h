/*
 * kvitems_async asynchronous iterable for ijson's C backend
 *
 * Contributed by Rodrigo Tobar <rtobar@icrar.org>
 *
 * ICRAR - International Centre for Radio Astronomy Research
 * (c) UWA - The University of Western Australia, 2020
 * Copyright by UWA (in the framework of the ICRAR)
 */

#ifndef KVITEMS_ASYNC_H
#define KVITEMS_ASYNC_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#if PY_VERSION_HEX >= 0x03050000
/**
 * kvitems_async asynchronous iterable object type
 */
extern PyTypeObject KVItemsAsync_Type;
#endif // PY_VERSION_HEX >= 0x03050000

#endif // KVITEMS_ASYNC_H