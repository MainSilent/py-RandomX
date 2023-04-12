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

#ifndef RANDOMX_H
#define RANDOMX_H

#include <stddef.h>
#include <stdint.h>

#define RANDOMX_HASH_SIZE 32
#define RANDOMX_DATASET_ITEM_SIZE 64

#ifndef RANDOMX_EXPORT
#define RANDOMX_EXPORT
#endif

typedef enum {
  RANDOMX_FLAG_DEFAULT = 0,
  RANDOMX_FLAG_LARGE_PAGES = 1,
  RANDOMX_FLAG_HARD_AES = 2,
  RANDOMX_FLAG_FULL_MEM = 4,
  RANDOMX_FLAG_JIT = 8,
  RANDOMX_FLAG_SECURE = 16,
  RANDOMX_FLAG_ARGON2_SSSE3 = 32,
  RANDOMX_FLAG_ARGON2_AVX2 = 64,
  RANDOMX_FLAG_ARGON2 = 96
} randomx_flags;

typedef struct randomx_dataset randomx_dataset;
typedef struct randomx_cache randomx_cache;


#if defined(__cplusplus)

#ifdef __cpp_constexpr
#define CONSTEXPR constexpr
#else
#define CONSTEXPR
#endif

inline CONSTEXPR randomx_flags operator |(randomx_flags a, randomx_flags b) {
	return static_cast<randomx_flags>(static_cast<int>(a) | static_cast<int>(b));
}
inline CONSTEXPR randomx_flags operator &(randomx_flags a, randomx_flags b) {
	return static_cast<randomx_flags>(static_cast<int>(a) & static_cast<int>(b));
}
inline randomx_flags& operator |=(randomx_flags& a, randomx_flags b) {
	return a = a | b;
}

extern "C" {
#endif

/**
 * @return The recommended flags to be used on the current machine.
 *         Does not include:
 *            RANDOMX_FLAG_LARGE_PAGES
 *            RANDOMX_FLAG_FULL_MEM
 *            RANDOMX_FLAG_SECURE
 *         These flags must be added manually if desired.
 *         On OpenBSD RANDOMX_FLAG_SECURE is enabled by default in JIT mode as W^X is enforced by the OS.
 */
RANDOMX_EXPORT randomx_flags randomx_get_flags(void);

/**
 * Creates a randomx_cache structure and allocates memory for RandomX Cache.
 *
 * @param flags is any combination of these 2 flags (each flag can be set or not set):
 *        RANDOMX_FLAG_LARGE_PAGES - allocate memory in large pages
 *        RANDOMX_FLAG_JIT - create cache structure with JIT compilation support; this makes
 *                           subsequent Dataset initialization faster
 *        Optionally, one of these two flags may be selected:
 *        RANDOMX_FLAG_ARGON2_SSSE3 - optimized Argon2 for CPUs with the SSSE3 instruction set
 *                                   makes subsequent cache initialization faster
 *        RANDOMX_FLAG_ARGON2_AVX2 - optimized Argon2 for CPUs with the AVX2 instruction set
 *                                   makes subsequent cache initialization faster
 *
 * @return Pointer to an allocated randomx_cache structure.
 *         Returns NULL if:
 *         (1) memory allocation fails
 *         (2) the RANDOMX_FLAG_JIT is set and JIT compilation is not supported on the current platform
 *         (3) an invalid or unsupported RANDOMX_FLAG_ARGON2 value is set
 */
RANDOMX_EXPORT randomx_cache *randomx_alloc_cache(randomx_flags flags);

/**
 * Initializes the cache memory and SuperscalarHash using the provided key value.
 * Does nothing if called again with the same key value.
 *
 * @param cache is a pointer to a previously allocated randomx_cache structure. Must not be NULL.
 * @param key is a pointer to memory which contains the key value. Must not be NULL.
 * @param keySize is the number of bytes of the key.
*/
RANDOMX_EXPORT void randomx_init_cache(randomx_cache *cache, const void *key, size_t keySize);

/**
 * Releases all memory occupied by the randomx_cache structure.
 *
 * @param cache is a pointer to a previously allocated randomx_cache structure.
*/
RANDOMX_EXPORT void randomx_release_cache(randomx_cache* cache);

/**
 * Creates a randomx_dataset structure and allocates memory for RandomX Dataset.
 *
 * @param flags is the initialization flags. Only one flag is supported (can be set or not set):
 *        RANDOMX_FLAG_LARGE_PAGES - allocate memory in large pages
 *
 * @return Pointer to an allocated randomx_dataset structure.
 *         NULL is returned if memory allocation fails.
 */
RANDOMX_EXPORT randomx_dataset *randomx_alloc_dataset(randomx_flags flags);

/**
 * Gets the number of items contained in the dataset.
 *
 * @return the number of items contained in the dataset.
*/
RANDOMX_EXPORT unsigned long randomx_dataset_item_count(void);

/**
 * Initializes dataset items.
 *
 * Note: In order to use the Dataset, all items from 0 to (randomx_dataset_item_count() - 1) must be initialized.
 * This may be done by several calls to this function using non-overlapping item sequences.
 *
 * @param dataset is a pointer to a previously allocated randomx_dataset structure. Must not be NULL.
 * @param cache is a pointer to a previously allocated and initialized randomx_cache structure. Must not be NULL.
 * @param startItem is the item number where intialization should start.
 * @param itemCount is the number of items that should be initialized.
*/
RANDOMX_EXPORT void randomx_init_dataset(randomx_dataset *dataset, randomx_cache *cache, unsigned long startItem, unsigned long itemCount);

/**
 * Returns a pointer to the internal memory buffer of the dataset structure. The size
 * of the internal memory buffer is randomx_dataset_item_count() * RANDOMX_DATASET_ITEM_SIZE.
 *
 * @param dataset is a pointer to a previously allocated randomx_dataset structure. Must not be NULL.
 *
 * @return Pointer to the internal memory buffer of the dataset structure.
*/
RANDOMX_EXPORT void *randomx_get_dataset_memory(randomx_dataset *dataset);

/**
 * Releases all memory occupied by the randomx_dataset structure.
 *
 * @param dataset is a pointer to a previously allocated randomx_dataset structure.
*/
RANDOMX_EXPORT void randomx_release_dataset(randomx_dataset *dataset);

#if defined(__cplusplus)
}
#endif

#endif
