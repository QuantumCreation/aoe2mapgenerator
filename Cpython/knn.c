#include <Python.h>
#include <math.h>

typedef struct {
    double x;
    double y;
} Point;

double distance(Point a, Point b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));
}

void swap(Point *a, Point *b) {
    Point temp = *a;
    *a = *b;
    *b = temp;
}

void heapify(Point arr[], int n, int i, Point p) {
    int largest = i;
    int l = 2*i + 1;
    int r = 2*i + 2;

    if (l < n && distance(arr[l], p) > distance(arr[largest], p))
        largest = l;

    if (r < n && distance(arr[r], p) > distance(arr[largest], p))
        largest = r;

    if (largest != i) {
        swap(&arr[i], &arr[largest]);
        heapify(arr, n, largest, p);
    }
}

void heapSort(Point arr[], int n, Point p) {
    for (int i = n / 2 - 1; i >= 0; i--)
        heapify(arr, n, i, p);

    for (int i=n-1; i>=0; i--) {
        swap(&arr[0], &arr[i]);
        heapify(arr, i, 0, p);
    }
}

PyObject* knn(PyObject* self, PyObject* args) {
    PyObject* listObj;
    double x;
    double y;
    int k;

    if (!PyArg_ParseTuple(args, "O!ddi", &PyList_Type, &listObj, &x, &y, &k)) {
        return NULL;
    }

    Point p = {x,y};

    Py_ssize_t n = PyList_Size(listObj);
    Point* arr = malloc(n * sizeof(Point));

    for (int i=0; i<n; i++) {
        PyObject* item = PyList_GetItem(listObj,i);
        double x = PyFloat_AsDouble(PyTuple_GetItem(item,0));
        double y = PyFloat_AsDouble(PyTuple_GetItem(item,1));
        arr[i] = (Point){x,y};
    }

    heapSort(arr,n,p);

    PyObject* result = PyList_New(k);
    for (int i=0; i<k; i++) {
        PyObject* point = PyTuple_New(2);
        PyTuple_SetItem(point,0,PyFloat_FromDouble(arr[i].x));
        PyTuple_SetItem(point,1,PyFloat_FromDouble(arr[i].y));
        PyList_SetItem(result,i,point);
    }

    free(arr);

    return result;
}

static PyMethodDef methods[] = {
   {"knn", knn, METH_VARARGS},
   {NULL,NULL}
};

static struct PyModuleDef moduledef = {
   PyModuleDef_HEAD_INIT,
   "knn",
   NULL,
   -1,
   methods
};

PyMODINIT_FUNC PyInit_knn(void) {
   return PyModule_Create(&moduledef);
}