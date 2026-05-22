import os

def combine_files(root_dir, output_file):
    ignored_dirs = {'dist', 'build', '__pycache__', '.git', '.gemini', 'venv', 'node_modules', 'static/uploads'}
    source_extensions = {'.py', '.pyw', '.js', '.css', '.html', '.json', '.bat', '.ps1', '.sql', '.txt'}
    # Ignore the output file itself if it already exists
    ignored_files = {os.path.basename(output_file), 'combine_code.py'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(root_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in source_extensions) and file not in ignored_files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"FILE: {rel_path}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"ERROR READING FILE: {e}\n")
                    
                    outfile.write("\n")

if __name__ == "__main__":
    current_dir = os.getcwd()
    output_path = os.path.join(current_dir, "FULL_CODE_ANALYSIS.txt")
    combine_files(current_dir, output_path)
    print(f"Combined code written to: {output_path}")
