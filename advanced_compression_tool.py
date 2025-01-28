from collections import Counter, defaultdict
import heapq
import pickle
from datetime import datetime
from typing import List, Dict, Tuple
from colorama import init, Fore, Back, Style
from tabulate import tabulate
import time

# Initialize colorama
init(autoreset=True)

# 1. Run-Length Encoding (RLE)
def rle_encode(input_str):
    """Encodes the input string using Run-Length Encoding."""
    encoded = []
    i = 0
    while i < len(input_str):
        count = 1
        while i + 1 < len(input_str) and input_str[i] == input_str[i + 1]:
            count += 1
            i += 1
        encoded.append(f"{input_str[i]}{count}")
        i += 1
    return ''.join(encoded)

def rle_decode(encoded_str):
    """Decodes an RLE-encoded string."""
    decoded = []
    i = 0
    while i < len(encoded_str):
        char = encoded_str[i]
        i += 1
        count = ""
        while i < len(encoded_str) and encoded_str[i].isdigit():
            count += encoded_str[i]
            i += 1
        decoded.append(char * int(count))
    return ''.join(decoded)

# 2. Huffman Coding
class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(freq_dict):
    """Builds a Huffman tree from a frequency dictionary."""
    heap = [HuffmanNode(char, freq) for char, freq in freq_dict.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0]

def generate_huffman_codes(tree):
    """Generates Huffman codes from the Huffman tree."""
    codes = {}

    def _generate_codes(node, current_code):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code
        _generate_codes(node.left, current_code + "0")
        _generate_codes(node.right, current_code + "1")

    _generate_codes(tree, "")
    return codes

def huffman_encode(input_str, codes):
    """Encodes the input string using Huffman codes."""
    return ''.join(codes[char] for char in input_str)


def huffman_decode(encoded_bits, code_table):
    # Reverse the code table for decoding: {code: symbol}
    reverse_table = {code: symbol for symbol, code in code_table.items()}

    decoded_output = []
    buffer = ""

    for bit in encoded_bits:
        buffer += bit
        if buffer in reverse_table:
            decoded_output.append(reverse_table[buffer])
            buffer = ""  # Reset buffer

    return ''.join(decoded_output)

def print_huffman_tree(node, prefix="", is_left=None):
    """Recursively prints the Huffman tree in a tree-like structure."""
    if is_left is None:
        print(Fore.CYAN + "Huffman Tree:")
    if node is not None:
        print(prefix + ("├── " if is_left else "└── ") + f"({node.char}: {node.freq})")
        print_huffman_tree(node.left, prefix + ("│   " if is_left else "    "), True)
        print_huffman_tree(node.right, prefix + ("│   " if is_left else "    "), False)

class HuffmanCompression:
    def __init__(self):
        self.huffman_tree = None
        self.huffman_codes = None

    def encode(self, text):
        freq_dict = Counter(text)
        print(Fore.GREEN + 'Frequency Dictionary:', freq_dict)
        

        self.huffman_tree = build_huffman_tree(freq_dict)
        print_huffman_tree(self.huffman_tree)
        

        self.huffman_codes = generate_huffman_codes(self.huffman_tree)
        print(Fore.GREEN + 'Huffman Codes:', self.huffman_codes)
        

        encoded = huffman_encode(text, self.huffman_codes)
        print(Fore.GREEN + 'Huffman Encoded:', encoded)
        
        return encoded

    def decode(self, encoded):
        decoded = huffman_decode(encoded, self.huffman_tree)
        print(Fore.YELLOW + 'Huffman Decoded:', decoded)
        
        return decoded

# 3. BWT Compression
def create_rotations(text: str) -> list[str]:
    """Create all possible rotations with animation data"""
    text = text + "$"
    n = len(text)
    rotations = []
    for i in range(n):
        rotation = text[i:] + text[:i]
        # self.rotations_history.append(rotation)
        rotations.append(rotation)
    return rotations

def bwt_encode(text):
    rotations = create_rotations(text)
    print(Fore.GREEN + 'All Rotations:', rotations)
    

    sorted_rotations = sorted(rotations)
    print(Fore.GREEN + 'Sorted Rotations:', sorted_rotations)
    

    encoded = ''.join(rotation[-1] for rotation in sorted_rotations)
    print(Fore.GREEN + 'BWT Encoded Result:', encoded)
    
    return encoded, rotations

def bwt_decode(bwt: str):
    iterations = []
    table = [''] * len(bwt)
    for i in range(len(bwt)):
        table = sorted([bwt[j] + table[j] for j in range(len(bwt))])
        print(Fore.YELLOW + f"Iteration {i + 1}: {table}")
        iterations.append(table)
        

    decoded = next(row[:-1] for row in table if row.endswith('$'))
    print(Fore.YELLOW + 'BWT Decoded Result:', decoded)
    
    return decoded, iterations

# 4. LZW Compression
class LZWCompression:
    def encode(self, text: str) -> List[int]:
        dictionary = {chr(i): i for i in range(256)}
        result = []
        current = ""
        code = 256

        for char in text:
            current_plus_char = current + char
            if current_plus_char in dictionary:
                current = current_plus_char
            else:
                result.append(dictionary[current])
                dictionary[current_plus_char] = code
                code += 1
                current = char

        if current:
            result.append(dictionary[current])

        print(Fore.GREEN + 'LZW Dictionary:', dictionary)
        

        print(Fore.GREEN + 'LZW Encoded Result:', result)
        

        return result

    def decode(self, compressed: List[int]) -> str:
        dictionary = {i: chr(i) for i in range(256)}
        result = []
        code = 256
        previous = chr(compressed[0])
        result.append(previous)

        for i in range(1, len(compressed)):
            current = compressed[i]
            if current in dictionary:
                s = dictionary[current]
            elif current == code:
                s = previous + previous[0]
            else:
                raise ValueError("Invalid compressed data")

            result.append(s)
            dictionary[code] = previous + s[0]
            code += 1
            previous = s

        decoded = ''.join(result)
        print(Fore.YELLOW + 'LZW Decoded Result:', decoded)
        

        return decoded

# 5. Compression UI
class CompressionUI:
    def __init__(self):
        self.compression_history = []
        self.current_stats = {}

    def display_menu(self):
        print(Fore.CYAN + "\n=== Advanced Compression System ===")
        print(Fore.YELLOW + "1. Compress using BWT")
        print(Fore.YELLOW + "2. Compress using Huffman")
        print(Fore.YELLOW + "3. Compress using LZW")
        print(Fore.YELLOW + "4. Compress using RLE")
        print(Fore.YELLOW + "5. View Compression History")
        print(Fore.YELLOW + "6. Exit")

    def compress_bwt(self):
        text = input(Fore.GREEN + "Enter the text to compress: ")
        bwt_result, rotations = bwt_encode(text)
        decoded_result = bwt_decode(bwt_result)
        self.save_compression_history(text, "BWT", bwt_result)

    def compress_huffman(self):
        text = input(Fore.GREEN + "Enter the text to compress: ")
        compressor = HuffmanCompression()
        huffman_result = compressor.encode(text)
        decoded_result = compressor.decode(huffman_result)
        self.save_compression_history(text, "Huffman", huffman_result)

    def compress_lzw(self):
        text = input(Fore.GREEN + "Enter the text to compress: ")
        compressor = LZWCompression()
        lzw_result = compressor.encode(text)
        decoded_result = compressor.decode(lzw_result)
        self.save_compression_history(text, "LZW", lzw_result)

    def compress_rle(self):
        text = input(Fore.GREEN + "Enter the text to compress: ")
        rle_result = rle_encode(text)
        print(Fore.GREEN + "RLE Encoded Result:", rle_result)
        

        decoded_result = rle_decode(rle_result)
        print(Fore.YELLOW + "RLE Decoded Result:", decoded_result)
        

        self.save_compression_history(text, "RLE", rle_result)

    def view_compression_history(self):
        if not self.compression_history:
            print(Fore.RED + "No compression history found.")
            return

        print(Fore.CYAN + "\n=== Compression History ===")
        headers = ["Date", "Algorithm", "Original Text", "Compressed Result"]
        rows = []
        for entry in self.compression_history:
            rows.append([entry['date'], entry['algorithm'], entry['original'], entry['compressed']])
        print(tabulate(rows, headers=headers, tablefmt="pretty"))
        

    def save_compression_history(self, original, algorithm, result):
        entry = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'algorithm': algorithm,
            'original': original,
            'compressed': str(result)
        }
        self.compression_history.append(entry)

        # Save to file
        with open('compression_history.pkl', 'wb') as f:
            pickle.dump(self.compression_history, f)

    def run(self):
        while True:
            self.display_menu()
            choice = input(Fore.GREEN + "Enter your choice: ")

            if choice == "1":
                self.compress_bwt()
            elif choice == "2":
                self.compress_huffman()
            elif choice == "3":
                self.compress_lzw()
            elif choice == "4":
                self.compress_rle()
            elif choice == "5":
                self.view_compression_history()
            elif choice == "6":
                print(Fore.CYAN + "Exiting the program. Goodbye!")
                break
            else:
                print(Fore.RED + "Invalid choice. Please try again.")

if __name__ == "__main__":
    ui = CompressionUI()
    ui.run()
