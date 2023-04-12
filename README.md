# py-RandomX

This is an old project to better understand the randomx algorithm for a hardware design.

The dataset is created with the original implementation.

## How to run

```sh
cd create_dataset
mkdir build && cd build
cmake ..
make
./gen-dataset

cd ../..
py tests.py
```