/*
Copyright (c) 2018-2019, tevador <tevador@gmail.com>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
	* Redistributions of source code must retain the above copyright
	  notice, this list of conditions and the following disclaimer.
	* Redistributions in binary form must reproduce the above copyright
	  notice, this list of conditions and the following disclaimer in the
	  documentation and/or other materials provided with the distribution.
	* Neither the name of the copyright holder nor the
	  names of its contributors may be used to endorse or promote products
	  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include "randomx.h"
#include "dataset.hpp"
#include "blake2/blake2.h"
#include <cassert>
#include <limits>
#include <cfenv>

extern "C" {

	randomx_flags randomx_get_flags() {
		randomx_flags flags = RANDOMX_FLAG_DEFAULT;
#ifdef RANDOMX_FORCE_SECURE
		if (flags == RANDOMX_FLAG_JIT) {
			flags |= RANDOMX_FLAG_SECURE;
		}
#endif
		return flags;
	}

	randomx_cache *randomx_alloc_cache(randomx_flags flags) {
		randomx_cache *cache = nullptr;
		auto impl = randomx::selectArgonImpl(flags);
		if (impl == nullptr) {
			return cache;
		}

		try {
			cache = new randomx_cache();
			cache->argonImpl = impl;
			switch ((int)(flags & (RANDOMX_FLAG_JIT | RANDOMX_FLAG_LARGE_PAGES))) {
				case RANDOMX_FLAG_DEFAULT:
					cache->dealloc = &randomx::deallocCache<randomx::DefaultAllocator>;
					cache->initialize = &randomx::initCache;
					cache->datasetInit = &randomx::initDataset;
					cache->memory = (uint8_t*)randomx::DefaultAllocator::allocMemory(randomx::CacheSize);
					break;

				default:
					UNREACHABLE;
			}
		}
		catch (std::exception &ex) {
			if (cache != nullptr) {
				randomx_release_cache(cache);
				cache = nullptr;
			}
		}
		if (cache && cache->memory == nullptr) {
			randomx_release_cache(cache);
			cache = nullptr;
		}

		return cache;
	}

	void randomx_init_cache(randomx_cache *cache, const void *key, size_t keySize) {
		assert(cache != nullptr);
		assert(keySize == 0 || key != nullptr);
		std::string cacheKey;
		cacheKey.assign((const char *)key, keySize);
		if (cache->cacheKey != cacheKey || !cache->isInitialized()) {
			cache->initialize(cache, key, keySize);
			cache->cacheKey = cacheKey;
		}
	}

	void randomx_release_cache(randomx_cache* cache) {
		assert(cache != nullptr);
		cache->dealloc(cache);
		delete cache;
	}

	randomx_dataset *randomx_alloc_dataset(randomx_flags flags) {

		//fail on 32-bit systems if DatasetSize is >= 4 GiB
		if (randomx::DatasetSize > std::numeric_limits<size_t>::max()) {
			return nullptr;
		}

		randomx_dataset *dataset = nullptr;

		try {
			dataset = new randomx_dataset();
			dataset->dealloc = &randomx::deallocDataset<randomx::LargePageAllocator>;
			dataset->memory = (uint8_t*)randomx::LargePageAllocator::allocMemory(randomx::DatasetSize);
		}
		catch (std::exception &ex) {
			if (dataset != nullptr) {
				randomx_release_dataset(dataset);
				dataset = nullptr;
			}
		}
		if (dataset && dataset->memory == nullptr) {
			randomx_release_dataset(dataset);
			dataset = nullptr;
		}

		return dataset;
	}

	constexpr unsigned long DatasetItemCount = randomx::DatasetSize / RANDOMX_DATASET_ITEM_SIZE;

	unsigned long randomx_dataset_item_count() {
		return DatasetItemCount;
	}

	void randomx_init_dataset(randomx_dataset *dataset, randomx_cache *cache, unsigned long startItem, unsigned long itemCount) {
		assert(dataset != nullptr);
		assert(cache != nullptr);
		assert(startItem < DatasetItemCount && itemCount <= DatasetItemCount);
		assert(startItem + itemCount <= DatasetItemCount);
		cache->datasetInit(cache, dataset->memory + startItem * randomx::CacheLineSize, startItem, startItem + itemCount);
	}

	void *randomx_get_dataset_memory(randomx_dataset *dataset) {
		assert(dataset != nullptr);
		return dataset->memory;
	}

	void randomx_release_dataset(randomx_dataset *dataset) {
		assert(dataset != nullptr);
		dataset->dealloc(dataset);
		delete dataset;
	}
}
