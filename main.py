import argparse
from tf_reader import TFReaderWin


if __name__ == "__main__":


    parser = argparse.ArgumentParser(description="Process a file")
    parser.add_argument("filename", help="trainings directory")
    args = parser.parse_args()
  


    filename = '../trainings'

    reader = TFReaderWin(args.filename)

    while reader.running:       

        reader.update_gui()