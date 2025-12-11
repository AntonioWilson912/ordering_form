from django import forms
from .models import Company
import csv
import io


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Active',
        }
        help_texts = {
            'is_active': 'Inactive companies will not appear when creating orders.',
        }


class BulkProductUploadForm(forms.Form):
    """Form for uploading products via CSV"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: Item No., Name, Type',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']

        # Check file extension
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError('File must be a CSV file (.csv extension)')

        # Check file size (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB')

        return csv_file

    def _is_empty_row(self, row, header_map):
        """Check if a row is effectively empty"""
        values = [
            (row.get(header_map.get('item no.')) or '').strip(),
            (row.get(header_map.get('name')) or '').strip(),
            (row.get(header_map.get('type')) or '').strip(),
        ]
        return all(v == '' for v in values)

    def parse_csv(self, company):
        """
        Parse CSV file and return list of product data with validation results.

        Returns:
            tuple: (valid_products, errors)
                valid_products: list of dicts with product data
                errors: list of dicts with row number and error messages
        """
        from product_app.models import Product

        csv_file = self.cleaned_data['csv_file']

        # Read and decode CSV
        try:
            decoded_file = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_file.seek(0)
                decoded_file = csv_file.read().decode('utf-8-sig')  # Try with BOM
            except UnicodeDecodeError:
                raise forms.ValidationError('File encoding not supported. Please use UTF-8.')

        csv_reader = csv.DictReader(io.StringIO(decoded_file))

        # Validate headers
        required_headers = {'Item No.', 'Name', 'Type'}
        actual_headers = set(csv_reader.fieldnames or [])

        # Handle case-insensitive and stripped headers
        normalize = lambda s: s.strip().lower() if s else ''
        normalized_actual = {normalize(h): h for h in actual_headers}
        normalized_required = {normalize(h) for h in required_headers}

        missing_headers = normalized_required - set(normalized_actual.keys())
        if missing_headers:
            # Map back to original case for error message
            original_missing = [h for h in required_headers
                              if normalize(h) in missing_headers]
            raise forms.ValidationError(
                f'Missing required columns: {", ".join(original_missing)}'
            )

        # Map normalized headers back to actual headers
        header_map = {
            'item no.': normalized_actual.get('item no.'),
            'name': normalized_actual.get('name'),
            'type': normalized_actual.get('type'),
        }

        valid_products = []
        errors = []
        row_num = 1  # Start at 1 (header is row 0)

        # Get existing products for this company
        # Create case-insensitive lookup dictionaries
        existing_products = Product.objects.filter(company=company).values('id', 'item_no', 'name')

        # Build lookup dictionaries
        existing_item_nos = {}  # Maps item_no -> product
        existing_names_lower = {}  # Maps name.lower() -> product

        for prod in existing_products:
            # Only track non-empty item numbers
            if prod['item_no'] and prod['item_no'].strip():
                existing_item_nos[prod['item_no'].strip()] = prod

            # Track all names (case-insensitive)
            if prod['name']:
                existing_names_lower[prod['name'].lower().strip()] = prod

        # Track items in current upload to detect duplicates within the CSV
        csv_item_nos = {}  # Maps item_no -> row_num
        csv_names_lower = {}  # Maps name.lower() -> row_num

        for row in csv_reader:
            row_num += 1

            # Check if row is empty - skip it
            if self._is_empty_row(row, header_map):
                continue

            row_errors = []

            # Extract values using mapped headers
            item_no = (row.get(header_map['item no.']) or '').strip()
            name = (row.get(header_map['name']) or '').strip()
            item_type = (row.get(header_map['type']) or '').strip().upper()

            # Validate name (required)
            if not name:
                row_errors.append('Name is required')
            elif len(name) < 2:
                row_errors.append('Name must be at least 2 characters')
            else:
                name_lower = name.lower()

                # Check against existing database records
                if name_lower in existing_names_lower:
                    existing_prod = existing_names_lower[name_lower]
                    row_errors.append(
                        f'Product name "{name}" already exists in database for this company '
                        f'(Product ID: {existing_prod["id"]})'
                    )
                # Check against other rows in this CSV
                elif name_lower in csv_names_lower:
                    row_errors.append(
                        f'Duplicate name "{name}" found in CSV (also on row {csv_names_lower[name_lower]})'
                    )

            # Validate item_no (optional but must be unique if provided)
            if item_no:  # Only validate if item_no is provided
                # Check against existing database records
                if item_no in existing_item_nos:
                    existing_prod = existing_item_nos[item_no]
                    row_errors.append(
                        f'Item No. "{item_no}" already exists in database for this company '
                        f'(Product: {existing_prod["name"]}, ID: {existing_prod["id"]})'
                    )
                # Check against other rows in this CSV
                elif item_no in csv_item_nos:
                    row_errors.append(
                        f'Duplicate Item No. "{item_no}" found in CSV (also on row {csv_item_nos[item_no]})'
                    )

            # Validate type (required, must be C or W)
            normalized_type = None
            if not item_type:
                row_errors.append('Type is required')
            elif item_type in ['C', 'W']:
                normalized_type = item_type
            elif item_type == 'CASE':
                normalized_type = 'C'
            elif item_type == 'WEIGHT':
                normalized_type = 'W'
            else:
                row_errors.append(
                    f'Type must be "C" (Case) or "W" (Weight). Got: "{item_type}"'
                )

            if row_errors:
                errors.append({
                    'row': row_num,
                    'data': {
                        'Item No.': item_no or '(empty)',
                        'Name': name or '(empty)',
                        'Type': item_type or '(empty)'
                    },
                    'errors': row_errors
                })
            else:
                valid_products.append({
                    'item_no': item_no,  # Can be empty string
                    'name': name,
                    'item_type': normalized_type,
                    'company': company
                })

                # Track for duplicate detection within CSV
                if item_no:  # Only track non-empty item numbers
                    csv_item_nos[item_no] = row_num
                csv_names_lower[name.lower()] = row_num

        if row_num == 1:
            raise forms.ValidationError('CSV file is empty (no data rows found)')

        return valid_products, errors