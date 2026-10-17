#!/usr/bin/env python3
"""
validate_catalog.py - Automated verification and linting tool for retail & e-commerce product catalogs.
Part of the bulk-product-verification skill.

Validates:
1. Standard package layout (products.json, catalog-map.json, research.json, exceptions.json, images/)
2. Product schema & field integrity (snake_case specs, localNames ta/ta-Latn, no sellingUnitVerified)
3. Zero-trust commercial defaults (pricePaise: 0, priceStatus: "confirm", stock: null, active: false, verified: false)
4. Selling basis & physical mechanics (mirrors ShopBot sellingBasisIssues contract)
5. Search taxonomy defense (flags brand or model pollution in category aliases)
6. Image existence, decodability, and < 2MB size limit
"""

import sys
import os
import json
import re
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

REQUIRED_FILES = ["products.json", "catalog-map.json", "research.json", "exceptions.json", "images"]
REQUIRED_PRODUCT_FIELDS = [
    "sku", "name", "localNames", "familyId", "brand", "specifications", "unit",
    "quantityStep", "sellingPolicy", "pricePaise", "priceStatus", "stock",
    "aliases", "keywords", "imagePath", "active", "verified"
]

SNAKE_CASE_REGEX = re.compile(r'^[a-z0-9]+(_[a-z0-9]+)*$')

MEASURED_UNITS = {'litre', 'kg', 'metre', 'foot'}
VOLUME_UNITS = {'litre', 'l', 'ml'}
WEIGHT_UNITS = {'kg', 'g'}

def canonical_unit(u: str) -> str:
    u = u.lower().strip()
    if u in ('litre', 'litres', 'liter', 'liters', 'l'):
        return 'litre'
    if u in ('ml', 'millilitre', 'millilitres'):
        return 'ml'
    if u in ('kg', 'kgs', 'kilogram', 'kilograms'):
        return 'kg'
    if u in ('g', 'gram', 'grams', 'gm'):
        return 'g'
    if u in ('metre', 'metres', 'meter', 'meters', 'm'):
        return 'metre'
    if u in ('foot', 'feet', 'ft'):
        return 'foot'
    return u

def unit_family(u: str):
    cu = canonical_unit(u)
    if cu in VOLUME_UNITS:
        return 'volume'
    if cu in WEIGHT_UNITS:
        return 'weight'
    if cu in {'metre', 'foot'}:
        return 'length'
    return None

def unit_scale(u: str) -> float:
    cu = canonical_unit(u)
    if cu in ('ml', 'g'):
        return 0.001
    return 1.0

class CatalogValidator:
    def __init__(self, catalog_dir: str):
        self.catalog_dir = Path(catalog_dir).resolve()
        self.errors = []
        self.warnings = []
        self.stats = {
            "products_count": 0,
            "images_verified": 0,
            "brands_found": set(),
            "families_found": set()
        }
        self.cat_map = None

    def error(self, sku: str, field: str, message: str):
        self.errors.append(f"[ERROR] [{sku}] {field}: {message}")

    def warn(self, sku: str, field: str, message: str):
        self.warnings.append(f"[WARN]  [{sku}] {field}: {message}")

    def validate(self) -> bool:
        print(f"--> Validating catalog package at: {self.catalog_dir}")
        if not self.check_folder_structure():
            return False

        self.validate_catalog_map()
        self.validate_products()
        self.validate_research_and_exceptions()

        self.report()
        return len(self.errors) == 0

    def check_folder_structure(self) -> bool:
        ok = True
        for req in REQUIRED_FILES:
            path = self.catalog_dir / req
            if not path.exists():
                self.errors.append(f"[STRUCTURE] Missing required file/directory: {req}")
                ok = False
        return ok

    def validate_catalog_map(self):
        map_path = self.catalog_dir / "catalog-map.json"
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                self.cat_map = json.load(f)
        except Exception as e:
            self.errors.append(f"[CATALOG-MAP] Failed to parse JSON: {e}")

    def check_selling_basis_issues(self, p: dict, sku: str):
        unit = p.get("unit", "")
        policy = p.get("sellingPolicy", {})
        if not isinstance(policy, dict):
            return

        sale_mode = policy.get("saleMode")
        contents = policy.get("packContents")

        # Check measured units vs pack mode
        if unit in MEASURED_UNITS:
            if sale_mode == "pack":
                self.error(sku, "sellingPolicy", f"Unit is measured '{unit}' but saleMode is 'pack'. Sealed pack needs count unit like can, bucket, bottle, box, or pack.")
        elif sale_mode == "measured":
            self.error(sku, "sellingPolicy", f"saleMode is 'measured' but unit '{unit}' is not in measured units {MEASURED_UNITS}.")

        # Check pack contents structure if provided
        if contents is not None:
            if not isinstance(contents, dict) or "value" not in contents or "unit" not in contents:
                self.error(sku, "sellingPolicy.packContents", "packContents must be an object with 'value' (number) and 'unit' (string)")
            else:
                c_val = contents.get("value")
                c_unit = str(contents.get("unit", ""))
                c_fam = unit_family(c_unit)
                u_fam = unit_family(unit)
                if c_fam and u_fam and c_fam != u_fam:
                    self.error(sku, "sellingPolicy.packContents", f"Pack unit '{c_unit}' ({c_fam}) and selling unit '{unit}' ({u_fam}) disagree on physical dimension.")

    def validate_products(self):
        prod_path = self.catalog_dir / "products.json"
        try:
            with open(prod_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            self.errors.append(f"[PRODUCTS] Failed to parse JSON: {e}")
            return

        if isinstance(raw_data, dict) and "products" in raw_data:
            products = raw_data["products"]
        elif isinstance(raw_data, list):
            products = raw_data
        else:
            self.errors.append(f"[PRODUCTS] Root must be an array of products or an object containing a 'products' array")
            return

        if not isinstance(products, list):
            self.errors.append(f"[PRODUCTS] 'products' must be a list of product records")
            return

        self.stats["products_count"] = len(products)
        skus_seen = set()

        for idx, p in enumerate(products):
            sku = p.get("sku", f"ITEM_INDEX_{idx}")
            if not p.get("sku"):
                self.error(sku, "sku", "Missing or empty sku")
            elif sku in skus_seen:
                self.error(sku, "sku", f"Duplicate SKU within batch: {sku}")
            skus_seen.add(sku)

            # Check required fields
            for rf in REQUIRED_PRODUCT_FIELDS:
                if rf not in p:
                    self.error(sku, rf, f"Missing required draft schema field '{rf}'")

            # Check rejected draft fields
            if "sellingUnitVerified" in p:
                self.error(sku, "sellingUnitVerified", "Forbidden field in draft import record")

            # Track brand & family
            brand = p.get("brand", "")
            if isinstance(brand, str) and brand.strip():
                self.stats["brands_found"].add(brand.strip().lower())
            family = p.get("familyId", "")
            if isinstance(family, str) and family.strip():
                self.stats["families_found"].add(family.strip())

            # Specifications keys must be snake_case
            specs = p.get("specifications", {})
            if isinstance(specs, dict):
                for k in specs.keys():
                    if not SNAKE_CASE_REGEX.match(k):
                        self.error(sku, f"specifications.{k}", f"Key '{k}' is not lowercase snake_case")
            else:
                self.error(sku, "specifications", "Must be a key-value object")

            # Local names
            ln = p.get("localNames", {})
            if isinstance(ln, dict):
                if "ta" not in ln:
                    self.warn(sku, "localNames.ta", "Missing Tamil script representation")
                if "ta-Latn" not in ln:
                    self.warn(sku, "localNames['ta-Latn']", "Missing Tanglish representation")
            else:
                self.error(sku, "localNames", "Must be an object with 'ta' and 'ta-Latn'")

            # Commercial zero-trust defaults
            if p.get("pricePaise") != 0 and not p.get("verified"):
                self.error(sku, "pricePaise", f"Draft record has unverified pricePaise: {p.get('pricePaise')}. Must be 0.")
            if p.get("priceStatus") != "confirm" and not p.get("verified"):
                self.error(sku, "priceStatus", f"Draft record priceStatus must be 'confirm', got: {p.get('priceStatus')}")
            if p.get("stock") is not None and not p.get("verified"):
                self.error(sku, "stock", f"Draft record stock must be null, got: {p.get('stock')}")
            if p.get("active") is not False:
                self.error(sku, "active", f"Draft record must have active: false")
            if p.get("verified") is not False:
                self.error(sku, "verified", f"Draft record must have verified: false prior to merchant review")

            # Selling policy mechanics
            self.check_selling_basis_issues(p, sku)

            # Image audit
            img_rel = p.get("imagePath", "")
            if not img_rel:
                self.error(sku, "imagePath", "Missing imagePath")
            else:
                img_path = self.catalog_dir / img_rel
                if not img_path.exists():
                    self.error(sku, "imagePath", f"Image file not found: {img_rel}")
                else:
                    self.stats["images_verified"] += 1
                    size_bytes = img_path.stat().st_size
                    if size_bytes > 2 * 1024 * 1024:
                        self.error(sku, "imagePath", f"Image exceeds 2 MB limit ({size_bytes} bytes)")
                    if HAS_PIL:
                        try:
                            with Image.open(img_path) as im:
                                im.verify()
                        except Exception as e:
                            self.error(sku, "imagePath", f"Image corrupted or unreadable: {e}")

        # Post-scan: taxonomy alias pollution check
        self.check_taxonomy_alias_pollution()

    def check_taxonomy_alias_pollution(self):
        if not self.cat_map:
            return

        nodes = []
        if isinstance(self.cat_map, dict):
            if "nodes" in self.cat_map and isinstance(self.cat_map["nodes"], list):
                nodes = self.cat_map["nodes"]
            else:
                for k, v in self.cat_map.items():
                    if isinstance(v, dict):
                        node = dict(v)
                        node["id"] = k
                        nodes.append(node)
        elif isinstance(self.cat_map, list):
            nodes = self.cat_map

        # Check if known brand names appear in category aliases
        known_brands = {b for b in self.stats["brands_found"] if len(b) > 2}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            fam_id = node.get("id", "unknown")
            aliases = node.get("aliases", [])
            for alias in aliases:
                alias_lower = str(alias).lower()
                for brand in known_brands:
                    pattern = r'\b' + re.escape(brand) + r'\b'
                    if re.search(pattern, alias_lower):
                        self.warn("TAXONOMY", f"family:{fam_id}",
                                  f"Category alias '{alias}' contains brand name '{brand}'. This causes search routing pollution!")

    def validate_research_and_exceptions(self):
        res_path = self.catalog_dir / "research.json"
        try:
            with open(res_path, "r", encoding="utf-8") as f:
                research = json.load(f)
            if not isinstance(research, (dict, list)):
                self.warn("RESEARCH", "format", "research.json should be a list or dict of research citations")
        except Exception as e:
            self.warn("RESEARCH", "parse", f"Could not parse research.json: {e}")

        exc_path = self.catalog_dir / "exceptions.json"
        try:
            with open(exc_path, "r", encoding="utf-8") as f:
                exceptions = json.load(f)
            if not isinstance(exceptions, (dict, list)):
                self.warn("EXCEPTIONS", "format", "exceptions.json should be a list or dict of unresolved merchant questions")
        except Exception as e:
            self.warn("EXCEPTIONS", "parse", f"Could not parse exceptions.json: {e}")

    def report(self):
        print("\n================ VALIDATION REPORT ================")
        print(f"Total Products Checked: {self.stats['products_count']}")
        print(f"Total Images Checked:   {self.stats['images_verified']}")
        print(f"Total Brands Found:     {len(self.stats['brands_found'])}")
        print(f"Errors Encountered:     {len(self.errors)}")
        print(f"Warnings Logged:        {len(self.warnings)}")
        print("===================================================\n")

        if self.errors:
            print("--- CRITICAL ERRORS ---")
            for err in self.errors[:30]:
                print(err)
            if len(self.errors) > 30:
                print(f"... and {len(self.errors) - 30} more errors.")
            print()

        if self.warnings:
            print("--- WARNINGS (Informational & Optimization) ---")
            for w in self.warnings[:20]:
                print(w)
            if len(self.warnings) > 20:
                print(f"... and {len(self.warnings) - 20} more warnings.")
            print()

        if len(self.errors) == 0:
            print("✅ SUCCESS: Package meets all draft schema, selling basis, and commercial honesty requirements.")
        else:
            print("❌ FAILURE: Resolve critical errors before attempting staging or import.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_catalog.py <catalog_package_directory>")
        sys.exit(1)

    target_dir = sys.argv[1]
    validator = CatalogValidator(target_dir)
    success = validator.validate()
    sys.exit(0 if success else 1)
