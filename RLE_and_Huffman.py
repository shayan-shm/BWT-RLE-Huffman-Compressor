from collections import Counter, defaultdict
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

def huffman_decode(encoded_str, tree):
    """Decodes a Huffman-encoded string using the Huffman tree."""
    decoded = []
    node = tree
    for bit in encoded_str:
        node = node.left if bit == "0" else node.right
        if node.char is not None:
            decoded.append(node.char)
            node = tree
    return ''.join(decoded)


def print_huffman_tree(node, prefix="", is_left=None):
    """Recursively prints the Huffman tree in a tree-like structure."""
    if is_left is None:
        print("Huffman Tree:")
    if node is not None:
        # Print the current node
        print(prefix + ("├── " if is_left else "└── ") + f"({node.char}: {node.freq})")

        # Recursively print the left and right children
        print_huffman_tree(node.left, prefix + ("│   " if is_left else "    "), True)
        print_huffman_tree(node.right, prefix + ("│   " if is_left else "    "), False)

def encode_bwt_output(bwt_string):
    print('rle_encoded:', rle_encoded := rle_encode(bwt_string))

    print('frequency_dictionary:', freq_dict := dict(Counter(rle_encoded)))

    global huffman_tree
    huffman_tree = build_huffman_tree(freq_dict)
    print_huffman_tree(huffman_tree)

    print('huffman_codes:', huffman_codes := generate_huffman_codes(huffman_tree))

    print('huffman_encoded:', huffman_encoded := huffman_encode(rle_encoded, huffman_codes))

    return huffman_encoded

def decode_to_bwt(encoded_str):
    print('huffman_decoded:', huffman_decoded := huffman_decode(encoded_str, huffman_tree))

    print('rle_decoded:', rle_decoded := rle_decode(huffman_decoded))

    return rle_decoded



# Main Execution
if __name__ == "__main__":

    string = encode_bwt_output('annb$aa')

    decode_to_bwt(string)

