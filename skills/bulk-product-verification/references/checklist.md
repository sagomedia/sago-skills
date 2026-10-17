# Pre-Import Catalog Gatekeeper Checklist

Use this 25-point checklist before staging or committing any bulk product catalog to draft proposals or database queues.

---

## 1. Package & File System Layout
- [ ] 1. Folder contains all 4 core data files: `products.json`, `catalog-map.json`, `research.json`, `exceptions.json`.
- [ ] 2. Folder contains an `images/` directory containing all referenced image assets.
- [ ] 3. All JSON files parse cleanly without syntax errors or trailing commas.
- [ ] 4. No temporary editor backups (`.swp`, `~`, `.bak`) exist in the package.

## 2. Schema & Field Conventions
- [ ] 5. All specification keys are lowercase `snake_case` (e.g. `pipe_class`, `joint_type`, `nominal_size`).
- [ ] 6. Multilingual representation is provided under `localNames.ta` (Tamil script) and `localNames["ta-Latn"]` (Tanglish).
- [ ] 7. No forbidden runtime fields are present (e.g., `sellingUnitVerified` must NOT appear on product records).
- [ ] 8. Stable SKUs are preserved; no arbitrary SKU renaming to fit transient path regexes.

## 3. Selling Basis & Physical Dimensions
- [ ] 9. Pack contents are explicitly decoupled from the ordered selling unit (e.g., `unit: "can"`, `sellingPolicy.packContents: { value: 4, unit: "litre" }`).
- [ ] 10. No volume-to-weight or weight-to-volume conversions (Litres are NEVER converted to Kilograms).
- [ ] 11. Measured sales units (`metre`, `kg`, `litre`, `foot`) are reserved strictly for loose or cut items.
- [ ] 12. Cutting policy defaults to `cutAllowed: false` on pipes, hoses, cables, and wire unless explicit merchant confirmation is documented.
- [ ] 13. Compound product packs (e.g. epoxy resin + hardener) record the total nominal net weight in `specifications.pack_size` and component breakdown in `specifications.composition`.

## 4. Visual Provenance & Image Integrity
- [ ] 14. Every `imagePath` resolves to an existing file in `images/`.
- [ ] 15. Every image file decodes cleanly and is strictly under the 2 MB threshold.
- [ ] 16. Image category matches product category (no hand saws pointing to chisels, no pliers pointing to vices).
- [ ] 17. Stamped, embossed, or printed measurements on product photos do NOT contradict product specifications (e.g., no 180mm label on a 20mm fitting).
- [ ] 18. AI-generated illustrations are inspected for hallucinated alphanumeric technical ratings; garbled media is excluded.
- [ ] 19. All AI-generated media is explicitly flagged `generated: true` and `identityPreserved: false`.
- [ ] 20. Lossy transformations (e.g., JPEG Quality 95 export) are accurately recorded in `image-edits.json` without false "lossless" claims.

## 5. Search Taxonomy & Category Defense
- [ ] 21. Category and family aliases in `catalog-map.json` are strictly generic. No brand names or specific model codes appear in category aliases.
- [ ] 22. Brand names belong strictly in product-level `brand`, `aliases`, and `keywords`.

## 6. Zero-Trust Commercial Honesty
- [ ] 23. Draft commercial defaults are strictly enforced: `pricePaise: 0`, `priceStatus: "confirm"`, `stock: null`, `active: false`, `verified: false`.
- [ ] 24. Internet prices from research are retained in `research.json` as research anchors only; never staged as merchant retail prices.

## 7. Multi-Batch Governance & Merchant Handoff
- [ ] 25. An actionable `OWNER-QUESTIONS.md` is compiled covering demo shortlist pricing, in-store cutting policies, and ambiguous physical variants.
