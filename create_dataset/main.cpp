#include "src/randomx.h"
#include <iostream>
#include <iomanip>

int main() {
	const char myKey[] = "test key 000";

	randomx_flags flags = randomx_get_flags();
	flags |= RANDOMX_FLAG_FULL_MEM;
	flags |= RANDOMX_FLAG_LARGE_PAGES;
	randomx_cache *myCache = randomx_alloc_cache(flags);
	if (myCache == nullptr) {
		std::cout << "Cache allocation failed" << std::endl;
		return 1;
	}
	randomx_init_cache(myCache, myKey, 12);

	randomx_dataset *myDataset = randomx_alloc_dataset(flags);
	if (myDataset == nullptr) {
		std::cout << "Dataset allocation failed" << std::endl;
		return 1;
	}

	auto datasetItemCount = randomx_dataset_item_count();
	randomx_init_dataset(myDataset, myCache, 0, datasetItemCount);
	randomx_release_cache(myCache);
	randomx_release_dataset(myDataset);

	return 0;
}