from collections import Counter
import heapq


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


class HuffmanCompression:
    def __init__(self):
        self.huffman_tree = None
        self.huffman_codes = None

    def encode(self, text):
        freq_dict = Counter(text)

        self.huffman_tree = build_huffman_tree(freq_dict)

        self.huffman_codes = generate_huffman_codes(self.huffman_tree)

        encoded = huffman_encode(text, self.huffman_codes)

        return encoded

    def decode(self, encoded):
        decoded = huffman_decode(encoded, self.huffman_tree)

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

    sorted_rotations = sorted(rotations)

    encoded = ''.join(rotation[-1] for rotation in sorted_rotations)

    return encoded, rotations


def bwt_decode(bwt: str):
    iterations = []
    table = [''] * len(bwt)
    for i in range(len(bwt)):
        table = sorted([bwt[j] + table[j] for j in range(len(bwt))])
        iterations.append(table)

    decoded = next(row[:-1] for row in table if row.endswith('$'))

    return decoded, iterations

