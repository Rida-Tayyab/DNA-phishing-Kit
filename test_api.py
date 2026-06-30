import requests
import sys
from pathlib import Path

def test_api():
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <path_to_zip_file>")
        return
    
    zip_file = Path(sys.argv[1])
    if not zip_file.exists():
        print(f"Error: File {zip_file} does not exist")
        return
    
    print(f"Testing API with {zip_file.name}...")
    
    try:
        with open(zip_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://127.0.0.1:8000/classify', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Classification successful!")
            print(f"   Predicted family: {result['predicted_family']}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Top 5 neighbors:")
            for i, (family, distance) in enumerate(result['top_5_neighbours'], 1):
                print(f"     {i}. {family} (distance: {distance:.3f})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server")
        print("   Make sure the server is running: cd api && python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()