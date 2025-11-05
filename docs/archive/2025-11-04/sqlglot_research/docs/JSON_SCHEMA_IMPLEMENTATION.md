# JSON Schema Implementation for Structured Outputs

## Current vs Improved Approach

### **Current (JSON Mode):**
```python
response_format={"type": "json_object"}
```
**Result:** Valid JSON, but AI can use any keys/structure

### **Improved (JSON Schema with Structured Outputs):**
```python
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "LineageInference",
        "strict": true,
        "schema": {
            "type": "object",
            "properties": {
                "input_procedures": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "output_procedures": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "reasoning": {
                    "type": "string"
                }
            },
            "required": ["input_procedures", "output_procedures", "confidence", "reasoning"],
            "additionalProperties": false
        }
    }
}
```
**Result:** **100% guaranteed** correct structure with exact keys!

---

## Benefits for Our Use Case

1. **Eliminates Empty Results with High Confidence**
   - AI MUST provide confidence value
   - AI MUST provide reasoning
   - No more `[]` with confidence 0.95!

2. **Guarantees Array Types**
   - input_procedures MUST be array (not string, not null)
   - output_procedures MUST be array
   - No more parsing errors

3. **Enforces Confidence Range**
   - Min: 0.0, Max: 1.0
   - AI can't return confidence 5.2 or -0.1

4. **Requires Reasoning**
   - AI MUST explain its decision
   - Helps debug why AI returned empty arrays

---

## Code Implementation

### **File:** `lineage_v3/parsers/ai_disambiguator.py`

**Replace lines 583-593:**

```python
# OLD CODE (current):
response = self.client.chat.completions.create(
    model=self.deployment,
    messages=[...],
    response_format={"type": "json_object"},  # Basic JSON mode
    temperature=0.0,
    max_tokens=2000,
    timeout=self.timeout
)
```

**NEW CODE (with JSON Schema):**

```python
# Define JSON Schema for lineage inference
lineage_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "LineageInferenceResponse",
        "strict": True,  # Enforce 100% compliance
        "schema": {
            "type": "object",
            "properties": {
                "input_procedures": {
                    "type": "array",
                    "description": "SPs that READ from this table",
                    "items": {
                        "type": "string",
                        "pattern": "^[A-Z_]+\\.[a-zA-Z0-9_]+$"  # schema.name format
                    }
                },
                "output_procedures": {
                    "type": "array",
                    "description": "SPs that WRITE to this table",
                    "items": {
                        "type": "string",
                        "pattern": "^[A-Z_]+\\.[a-zA-Z0-9_]+$"  # schema.name format
                    }
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0.0 and 1.0",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of the inference decision",
                    "minLength": 10,
                    "maxLength": 500
                }
            },
            "required": ["input_procedures", "output_procedures", "confidence", "reasoning"],
            "additionalProperties": False
        }
    }
}

response = self.client.chat.completions.create(
    model=self.deployment,
    messages=[
        {"role": "system", "content": self._get_inference_system_prompt()},
        {"role": "user", "content": prompt}
    ],
    response_format=lineage_schema,  # Use JSON Schema instead of basic JSON mode
    temperature=0.0,
    max_tokens=2000,
    timeout=self.timeout
)
```

---

## Expected Improvements

### **Before (Basic JSON Mode):**
```
Test Results:
- Empty arrays with high confidence: 78/84 (93%)
- Missing reasoning: frequent
- Incorrect confidence values: occasional
```

### **After (JSON Schema with Structured Outputs):**
```
Expected Results:
- Empty arrays with explanation: AI MUST explain why empty
- Missing reasoning: IMPOSSIBLE (required field)
- Incorrect confidence values: IMPOSSIBLE (enforced 0.0-1.0)
- Overall: Better debugging capability
```

---

## Additional Schema Constraints

### **Option 1: Stricter SP Name Format**
```python
"pattern": "^(CONSUMPTION_|STAGING_|ADMIN\\.|dbo\\.)[a-zA-Z0-9_]+$"
```
**Benefit:** Ensures schema.name format matches our conventions

### **Option 2: Enum for Confidence Levels**
```python
"confidence": {
    "type": "number",
    "enum": [0.0, 0.75, 0.80, 0.85, 0.90, 0.95]
}
```
**Benefit:** Forces AI to use standard confidence levels from few-shot examples

### **Option 3: Longer Reasoning (for debugging)**
```python
"reasoning": {
    "type": "string",
    "minLength": 20,
    "maxLength": 200
}
```
**Benefit:** AI must provide substantive reasoning

---

## Testing Plan

### Step 1: Implement JSON Schema (5 minutes)
- Update ai_disambiguator.py with new response_format
- Add schema definition

### Step 2: Test on 10 Tables (2 minutes)
- Run parser on small sample
- Verify schema compliance
- Check if reasoning is always provided

### Step 3: Full Test on 176 Tables (5 minutes)
- Run complete test
- Compare with previous results
- Analyze reasoning for empty arrays

### Step 4: Iterate if Needed
- If AI still returns too many empty arrays, adjust few-shot
- If confidence values are wrong, add enum constraint

---

## Implementation Priority

### **High Priority (Do First):**
1. ✅ Add JSON Schema with basic structure
2. ✅ Require all 4 fields (input_procedures, output_procedures, confidence, reasoning)
3. ✅ Set additionalProperties: false

### **Medium Priority (Add if Needed):**
4. ⏳ Add pattern validation for SP names
5. ⏳ Add minLength for reasoning (ensure substantive explanation)
6. ⏳ Add confidence enum (standardize levels)

### **Low Priority (Nice to Have):**
7. ⏳ Add maxLength constraints
8. ⏳ Add description fields for better AI understanding

---

## Estimated Impact

**Current Issue:** AI returns empty arrays without explanation (93% of cases)

**With JSON Schema:**
- ✅ AI MUST provide reasoning for empty arrays
- ✅ We can debug WHY AI thinks there's no match
- ✅ 100% schema compliance (no parsing errors)

**Expected:** Still low match rate, BUT we'll understand why and can improve few-shot based on reasoning

---

**Next Action:** Implement JSON Schema in ai_disambiguator.py

**Timeline:** 15 minutes (5 min code + 10 min test)
