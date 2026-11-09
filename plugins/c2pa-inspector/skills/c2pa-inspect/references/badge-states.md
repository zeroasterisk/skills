# Badge States and Validation Criteria

This reference outlines the three C2PA badge states, validation status codes, exit code semantics, and cryptographic trust evaluation.

---

## 1. Badge States Overview

A media asset evaluated for C2PA provenance resolves to one of three badge states:

```text
               +-----------------------------+
               |      File Submitted         |
               +-----------------------------+
                              |
                     [ Has C2PA Manifest? ]
                     /                    \
                   No                      Yes
                  /                          \
        +-----------------+            [ Signature & Hash Valid? ]
        |    UNSIGNED     |            /                         \
        | (Exit Code: 1)  |          No                           Yes
        +-----------------+         /                               \
                           +-----------------+              +-----------------+
                           |     INVALID     |              |     SIGNED      |
                           | (Exit Code: 2)  |              | (Exit Code: 0)  |
                           +-----------------+              +-----------------+
```

### 1. `SIGNED` (Valid Content Credentials)
- **Description:** The media asset contains a valid, well-formed C2PA manifest store.
- **Criteria:** The claim signature verifies against the signing certificate, the media byte hash matches the manifest assertion, and no fatal validation errors exist.
- **Exit Code:** `0`

### 2. `UNSIGNED` (No Content Credentials)
- **Description:** The media asset contains no C2PA manifest store or JUMBF metadata.
- **Criteria:** The file was parsed successfully as a valid media container (e.g. JPEG, PNG, MP4), but no provenance headers or Content Credentials boxes were detected.
- **Exit Code:** `1` (or `0` when running broad informational scans)

### 3. `INVALID` (Validation Failure or Tampering)
- **Description:** The media asset contains C2PA metadata, but validation failed.
- **Criteria:** Triggered by any fatal error, such as a hash mismatch (file altered after signing), expired or untrusted certificate, revoked credential, or corrupted JUMBF block.
- **Exit Code:** `2`

---

## 2. Common Validation Status Codes

| Status Code | Severity | Explanation |
|---|---|---|
| `claimSignature.validated` | Success | The digital signature over the claim is cryptographically valid. |
| `signingCredential.trusted` | Success | The signing certificate chains to a trusted root in the trust store. |
| `assertion.hashedURI.match` | Success | Assertion byte hashes match manifest declarations. |
| `hash.data.mismatch` | Error | The media file content was modified after the manifest was signed. |
| `claimSignature.invalid` | Error | The signature cannot be verified with the embedded public key. |
| `signingCredential.untrusted` | Warning / Error | Certificate valid, but root CA is not present in local trust anchors. |
| `timestamp.mismatch` | Warning | The RFC 3161 timestamp could not be verified against the TSA anchor. |

---

## 3. Trust Anchor Verification

Google Credentio supports two independent trust anchor sets:

1. **Claim Signer Trust Anchors:** PEM-encoded root and intermediate certificates used to verify the signer who authored the claim.
2. **Time-Stamp Authority (TSA) Trust Anchors:** PEM-encoded certificates used to verify RFC 3161 timestamps attached to the signature.

When evaluating files in testing or development environments without local root certificates, pass `--skip-trust-checks` (the default) to verify signature mathematics and hash integrity without failing on unknown certificate authorities.
