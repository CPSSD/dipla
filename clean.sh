echo "Removing all __pycache__ directories..."
find . -name \*__pycache__ -delete

echo "Removing all compiled python files..."
find . -name \*.pyc -delete

echo "Removing all executable files..."
find . -name \*.exe -delete

echo "Removing all log files..."
find . -name \*.log -delete

echo "Done."
