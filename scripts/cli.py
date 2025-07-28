
import subprocess
import os
import sys

def main():
    # Get the absolute path to the project's root directory.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Add the 'src' directory to the Python path.
    src_path = os.path.join(project_root, 'src')
    sys.path.insert(0, src_path)

    # Get a list of all python files in the current directory, excluding this one.
    script_dir = os.path.dirname(__file__)
    files = [f for f in os.listdir(script_dir) if f.endswith('.py') and f != os.path.basename(__file__)]

    while True:
        # Print a numbered list of the files.
        for i, file in enumerate(files):
            print(f'{i+1}. {file}')

        # Prompt the user to select a file.
        selection = input('Enter the number of the file to run, or q to quit: ')

        # If the user entered 'q', quit the program.
        if selection == 'q':
            break

        # Otherwise, try to convert the selection to an integer.
        try:
            selection = int(selection)
        except ValueError:
            print('Invalid selection.')
            continue

        # If the selection is valid, run the corresponding file.
        if 1 <= selection <= len(files):
            # Run the selected script.
            script_path = os.path.join(script_dir, files[selection-1])
            env = os.environ.copy()
            env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')
            subprocess.run([sys.executable, script_path], env=env)
        else:
            print('Invalid selection.')

if __name__ == '__main__':
    main()
