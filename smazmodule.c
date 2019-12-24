#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "smaz/smaz.h"

static PyObject *
py_smaz_compress(PyObject *self, PyObject *args)
{
    char *uncompressed_input;
    if (!PyArg_ParseTuple(args, "s", &uncompressed_input))
    {
        return NULL;
    }

    int output_length = 4096;
    char *compressed_output = (char *)malloc(output_length);
    int compressed_length = smaz_compress(uncompressed_input, strlen(uncompressed_input), compressed_output, output_length);
    // If the string didn't fit into the 4096, we will get 4097 returned. So, we continue
    // compressing with the rest
    while (output_length + 1 == compressed_length)
    {
        // increase string size
        output_length *= 2;
        compressed_output = (char *)realloc(compressed_output, output_length);
        // continue compressing
        compressed_length = smaz_compress(uncompressed_input, strlen(uncompressed_input), compressed_output, output_length);
    }
    compressed_output[output_length] = 0;

    // TODO: maybe y (bytes obj) make more sense?
    PyObject *string_object = Py_BuildValue("s", compressed_output);
    free(compressed_output);
    return string_object;
}

static PyMethodDef SmazMethods[] = {
    {"compress", py_smaz_compress, METH_VARARGS,
     "Compresses a string using SMAZ compression."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef smazmodule = {
    PyModuleDef_HEAD_INIT,
    "smaz",                                  /* name of module */
    "String compression library using SMAZ", /* module documentation, may be NULL */
    -1,                                      /* size of per-interpreter state of the
                                                module, or -1 if the module keeps
                                                state in global variables. */
    SmazMethods};

PyMODINIT_FUNC
PyInit_smaz(void)
{
    return PyModule_Create(&smazmodule);
}
