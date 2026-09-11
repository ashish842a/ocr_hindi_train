#!/usr/bin/env python3
"""
GPU availability test script
Tests if GPU is accessible in the current environment
"""

def test_cuda():
    """Test general CUDA availability"""
    print("=" * 50)
    print("Testing CUDA availability...")
    print("=" * 50)
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  Memory allocated: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
                print(f"  Memory cached: {torch.cuda.memory_reserved(i) / 1024**3:.2f} GB")
                print(f"  Total memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")

            # Test actual GPU computation
            print("\nTesting GPU computation...")
            device = torch.device("cuda")
            x = torch.randn(1000, 1000).to(device)
            y = torch.randn(1000, 1000).to(device)
            z = torch.matmul(x, y)
            print(f"✓ Successfully performed matrix multiplication on GPU")
            print(f"  Result device: {z.device}")
        else:
            print("⚠ CUDA is not available")
    except ImportError:
        print("PyTorch is not installed")
    except Exception as e:
        print(f"Error testing CUDA: {e}")

def test_tensorflow():
    """Test TensorFlow GPU availability"""
    print("\n" + "=" * 50)
    print("Testing TensorFlow GPU...")
    print("=" * 50)
    try:
        import tensorflow as tf
        print(f"TensorFlow version: {tf.__version__}")

        gpus = tf.config.list_physical_devices('GPU')
        print(f"Number of GPUs available: {len(gpus)}")

        if gpus:
            for gpu in gpus:
                print(f"GPU: {gpu}")
                details = tf.config.experimental.get_device_details(gpu)
                print(f"  Details: {details}")

            # Test actual GPU computation
            print("\nTesting GPU computation...")
            with tf.device('/GPU:0'):
                a = tf.random.normal([1000, 1000])
                b = tf.random.normal([1000, 1000])
                c = tf.matmul(a, b)
            print(f"✓ Successfully performed matrix multiplication on GPU")
        else:
            print("⚠ No GPU devices found in TensorFlow")

    except ImportError:
        print("TensorFlow is not installed")
    except Exception as e:
        print(f"Error testing TensorFlow: {e}")

def test_nvidia_smi():
    """Test nvidia-smi command"""
    print("\n" + "=" * 50)
    print("Testing nvidia-smi...")
    print("=" * 50)
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("⚠ nvidia-smi failed")
            print(result.stderr)
    except FileNotFoundError:
        print("⚠ nvidia-smi command not found")
    except Exception as e:
        print(f"Error running nvidia-smi: {e}")

if __name__ == "__main__":
    print("\n🔍 GPU Availability Test\n")

    test_cuda()
    test_tensorflow()
    test_nvidia_smi()

    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)
