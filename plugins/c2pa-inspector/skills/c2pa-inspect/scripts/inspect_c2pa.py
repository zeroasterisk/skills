#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""inspect_c2pa.py: Dual-engine C2PA Content Credentials inspector and batch auditor.

Built on Google Credentio data models and C-ABI, providing single-asset inspection,
multi-file batch auditing, recursive directory scanning, and AI provenance checks.
"""

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import glob
import json
import os
from pathlib import Path
import platform
import struct
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# ============================================================================
# 1. Models and Taxonomies (Repurposed from credentio.models)
# ============================================================================

class BadgeState(str, Enum):
    SIGNED = "signed"
    UNSIGNED = "unsigned"
    INVALID = "invalid"

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class AssertionKind(str, Enum):
    ACTIONS = "actions"
    INGREDIENT = "ingredient"
    THUMBNAIL = "thumbnail"
    AI_TRAINING_MINING = "ai_training_mining"
    METADATA = "metadata"
    HASH = "hash"
    OTHER = "other"

    @classmethod
    def classify(cls, label: str) -> "AssertionKind":
        lowered = label.lower()
        if "action" in lowered:
            return cls.ACTIONS
        if "ingredient" in lowered:
            return cls.INGREDIENT
        if "thumbnail" in lowered:
            return cls.THUMBNAIL
        if "training-mining" in lowered or "ai" in lowered:
            return cls.AI_TRAINING_MINING
        if "hash" in lowered:
            return cls.HASH
        if "metadata" in lowered or "exif" in lowered or "xmp" in lowered:
            return cls.METADATA
        return cls.OTHER

@dataclass
class SignatureInfo:
    issuer: Optional[str] = None
    algorithm: Optional[str] = None
    time: Optional[datetime] = None
    cert_chain_summary: Optional[str] = None

@dataclass
class Assertion:
    label: str
    kind: AssertionKind
    summary: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class ValidationStatus:
    code: str
    explanation: Optional[str] = None
    url: Optional[str] = None
    severity: Severity = Severity.INFO

@dataclass
class Manifest:
    label: str
    title: Optional[str] = None
    format: Optional[str] = None
    claim_generator: Optional[str] = None
    is_update_manifest: bool = False
    signature: Optional[SignatureInfo] = None
    assertions: List[Assertion] = field(default_factory=list)
    validation_statuses: List[ValidationStatus] = field(default_factory=list)
    ai_provenance: Optional[Dict[str, Any]] = None

    @property
    def overall_validity(self) -> BadgeState:
        if any(s.severity == Severity.ERROR for s in self.validation_statuses):
            return BadgeState.INVALID
        return BadgeState.SIGNED

@dataclass
class ProvenanceReport:
    asset_path: str
    engine_id: str
    engine_name: str
    has_credentials: bool
    badge: BadgeState
    elapsed_seconds: float
    core_seconds: Optional[float] = None
    media_type: Optional[str] = None
    spec_version: Optional[str] = None
    byte_size: int = 0
    active_manifest: Optional[Manifest] = None
    manifest_count: int = 0
    error_message: Optional[str] = None

# ============================================================================
# 2. Schema-Resilient Parser (Handles C2PA v1, v2, camelCase, snake_case)
# ============================================================================

def parse_crjson(
    raw_json: Union[str, Dict[str, Any]],
    media_type: Optional[str] = None,
    elapsed_seconds: float = 0.0,
    core_seconds: Optional[float] = None,
    asset_path: str = ""
) -> ProvenanceReport:
    """Parses Credentio-compatible JSON output into a structured ProvenanceReport."""
    try:
        data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
    except Exception as e:
        return ProvenanceReport(
            asset_path=asset_path,
            engine_id="credentio_parser",
            engine_name="Credentio Parser",
            has_credentials=False,
            badge=BadgeState.INVALID,
            elapsed_seconds=elapsed_seconds,
            error_message=f"JSON parse error: {e}"
        )

    manifests_raw = data.get("manifests", [])
    val_results = data.get("validation_results", {}) or data.get("validationResults", {})

    spec_version = (
        data.get("spec_version") or
        val_results.get("spec_version") or
        val_results.get("specVersion")
    )
    media_type = media_type or data.get("media_type") or val_results.get("media_type")

    manifest_objs: List[Manifest] = []

    for m in manifests_raw:
        label = m.get("label", "urn:c2pa:manifest")
        title = m.get("title")
        fmt = m.get("format")

        # Claim resolution: claim, claim.v2, or root level
        claim = m.get("claim", {}) or m.get("claim.v2", {})

        # Generator resolution
        generator = None
        gen_info = claim.get("claim_generator_info") or claim.get("claimGeneratorInfo")
        if isinstance(gen_info, list) and gen_info:
            first_gen = gen_info[0]
            if isinstance(first_gen, dict):
                generator = f"{first_gen.get('name', '')} {first_gen.get('version', '')}".strip()
        elif isinstance(gen_info, dict):
            generator = f"{gen_info.get('name', '')} {gen_info.get('version', '')}".strip()
        if not generator:
            generator = claim.get("claim_generator") or claim.get("claimGenerator")

        # Signature resolution
        sig_info = claim.get("signature_info", {}) or claim.get("signatureInfo", {})
        issuer = sig_info.get("issuer")
        if isinstance(issuer, dict):
            issuer = issuer.get("CN") or issuer.get("commonName")
        if not issuer and "certificateInfo" in sig_info:
            cert_info = sig_info.get("certificateInfo", {})
            issuer_obj = cert_info.get("issuer", {})
            issuer = issuer_obj.get("CN") if isinstance(issuer_obj, dict) else str(issuer_obj)
        if not issuer:
            issuer = sig_info.get("common_name") or sig_info.get("commonName")

        algorithm = sig_info.get("alg") or sig_info.get("algorithm")

        signing_time = None
        time_str = sig_info.get("time")
        if not time_str and "timeStampInfo" in sig_info:
            time_str = sig_info.get("timeStampInfo", {}).get("timestamp")
        if time_str:
            try:
                signing_time = datetime.fromisoformat(str(time_str).replace("Z", "+00:00"))
            except Exception:
                pass

        cert_serial = sig_info.get("cert_serial_number") or sig_info.get("serialNumber")
        if not cert_serial and "certificateInfo" in sig_info:
            cert_serial = sig_info.get("certificateInfo", {}).get("serialNumber")

        sig_obj = SignatureInfo(
            issuer=issuer,
            algorithm=algorithm,
            time=signing_time,
            cert_chain_summary=cert_serial
        )

        # Assertions resolution
        assertions_list: List[Assertion] = []
        ai_provenance: Dict[str, Any] = {}

        raw_assertions = m.get("assertions", {})
        if isinstance(raw_assertions, dict):
            for a_label, a_data in raw_assertions.items():
                kind = AssertionKind.classify(a_label)
                summary = None
                if isinstance(a_data, dict):
                    if "actions" in a_data and isinstance(a_data["actions"], list):
                        act_names = [x.get("action", "") for x in a_data["actions"] if isinstance(x, dict)]
                        summary = ", ".join(act_names)
                        # Check digitalSourceType
                        for x in a_data["actions"]:
                            dst = x.get("digitalSourceType") or x.get("digital_source_type")
                            if dst:
                                ai_provenance["digital_source_type"] = dst
                    elif "entries" in a_data:
                        entries = a_data["entries"]
                        if isinstance(entries, dict):
                            summary = "; ".join(f"{k}: {v.get('use', '') if isinstance(v, dict) else v}" for k, v in entries.items())
                            ai_provenance["training_mining"] = entries
                    elif "hash_value" in a_data:
                        summary = str(a_data["hash_value"])[:16] + "..."
                    elif "model" in a_data:
                        model_info = a_data.get("model", {})
                        ai_provenance["generative_model"] = model_info
                        if "prompt" in a_data:
                            ai_provenance["prompt"] = a_data.get("prompt")
                        summary = f"Model: {model_info.get('name', '')} {model_info.get('version', '')}".strip()

                assertions_list.append(Assertion(label=a_label, kind=kind, summary=summary, data=a_data if isinstance(a_data, dict) else None))
        elif isinstance(raw_assertions, list):
            for a_entry in raw_assertions:
                if isinstance(a_entry, dict):
                    a_label = a_entry.get("label", "assertion")
                    a_data = a_entry.get("data", {})
                    kind = AssertionKind.classify(a_label)
                    summary = None
                    if isinstance(a_data, dict):
                        if "actions" in a_data and isinstance(a_data["actions"], list):
                            act_names = [x.get("action", "") for x in a_data["actions"] if isinstance(x, dict)]
                            summary = ", ".join(act_names)
                            for x in a_data["actions"]:
                                dst = x.get("digitalSourceType") or x.get("digital_source_type")
                                if dst:
                                    ai_provenance["digital_source_type"] = dst
                        elif "entries" in a_data:
                            entries = a_data["entries"]
                            if isinstance(entries, dict):
                                summary = "; ".join(f"{k}: {v.get('use', '') if isinstance(v, dict) else v}" for k, v in entries.items())
                                ai_provenance["training_mining"] = entries
                        elif "hash_value" in a_data:
                            summary = str(a_data["hash_value"])[:16] + "..."
                    assertions_list.append(Assertion(label=a_label, kind=kind, summary=summary, data=a_data if isinstance(a_data, dict) else None))

        # Check explicit digital source type assertion
        if "c2pa.digital_source_type" in raw_assertions:
            dst_data = raw_assertions["c2pa.digital_source_type"]
            if isinstance(dst_data, dict):
                ai_provenance["digital_source_type"] = dst_data.get("type") or dst_data.get("digitalSourceType")

        # Validation status resolution
        status_list: List[ValidationStatus] = []
        val_sec = m.get("validation", {})
        statuses_raw = val_sec.get("status", []) if isinstance(val_sec, dict) else []
        for s in statuses_raw:
            if isinstance(s, dict):
                code = s.get("code", "")
                explanation = s.get("explanation")
                sev = Severity.ERROR if ("invalid" in code.lower() or "mismatch" in code.lower() or "error" in code.lower()) else Severity.INFO
                status_list.append(ValidationStatus(code=code, explanation=explanation, severity=sev))

        # Check v2 validationResults
        v2_results = m.get("validationResults", {}) or val_results
        if isinstance(v2_results, dict):
            for item in v2_results.get("failure", []):
                if isinstance(item, dict):
                    status_list.append(ValidationStatus(code=item.get("code", ""), explanation=item.get("explanation"), severity=Severity.ERROR))
            for item in v2_results.get("success", []):
                if isinstance(item, dict):
                    status_list.append(ValidationStatus(code=item.get("code", ""), explanation=item.get("explanation"), severity=Severity.INFO))
            for item in v2_results.get("informational", []):
                if isinstance(item, dict):
                    status_list.append(ValidationStatus(code=item.get("code", ""), explanation=item.get("explanation"), severity=Severity.INFO))

        manifest_objs.append(Manifest(
            label=label,
            title=title,
            format=fmt,
            claim_generator=generator,
            is_update_manifest=False,
            signature=sig_obj,
            assertions=assertions_list,
            validation_statuses=status_list,
            ai_provenance=ai_provenance if ai_provenance else None
        ))

    has_credentials = len(manifest_objs) > 0
    active_m = manifest_objs[0] if manifest_objs else None
    badge = BadgeState.UNSIGNED if not has_credentials else active_m.overall_validity

    return ProvenanceReport(
        asset_path=asset_path,
        engine_id="credentio_parser",
        engine_name="Credentio Parser",
        has_credentials=has_credentials,
        badge=badge,
        elapsed_seconds=elapsed_seconds,
        core_seconds=core_seconds,
        media_type=media_type,
        spec_version=spec_version,
        active_manifest=active_m,
        manifest_count=len(manifest_objs)
    )

# ============================================================================
# 3. Media Sniffing & Pure-Python Container Inspection Fallback
# ============================================================================

def sniff_media_type(header: bytes) -> Optional[str]:
    """Sniffs standard MIME types from initial file magic bytes."""
    if len(header) >= 3 and header[:3] == b"ID3":
        return "audio/mpeg"
    if len(header) >= 4 and header[:4] == b"fLaC":
        return "audio/flac"
    if len(header) >= 3 and header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(header) >= 8 and header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(header) >= 6 and (header[:6] == b"GIF87a" or header[:6] == b"GIF89a"):
        return "image/gif"
    if len(header) >= 4 and header[:4] == b"%PDF":
        return "application/pdf"
    if len(header) >= 12 and header[:4] == b"RIFF":
        form = header[8:12]
        if form == b"WAVE":
            return "audio/wav"
        if form == b"WEBP":
            return "image/webp"
        if form == b"AVI ":
            return "video/x-msvideo"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in (b"avif", b"avis"):
            return "image/avif"
        if brand in (b"heic", b"heix", b"mif1"):
            return "image/heic"
        if brand == b"M4A ":
            return "audio/mp4"
        return "video/mp4"
    return None

def inspect_media_fallback(path: Path) -> ProvenanceReport:
    """Pure-Python Credentio media container and JUMBF parser fallback."""
    start_time = time.perf_counter()
    file_size = path.stat().st_size

    if path.suffix.lower() == ".json":
        # Direct C2PA manifest JSON or test fixture inspection
        try:
            content = path.read_text(encoding="utf-8")
            report = parse_crjson(content, elapsed_seconds=time.perf_counter() - start_time, asset_path=str(path.resolve()))
            report.byte_size = file_size
            report.engine_id = "credentio_fixture_parser"
            report.engine_name = "Credentio Manifest Parser"
            return report
        except Exception as e:
            return ProvenanceReport(
                asset_path=str(path.resolve()),
                engine_id="credentio_fixture_parser",
                engine_name="Credentio Manifest Parser",
                has_credentials=False,
                badge=BadgeState.INVALID,
                elapsed_seconds=time.perf_counter() - start_time,
                byte_size=file_size,
                error_message=str(e)
            )

    try:
        with open(path, "rb") as f:
            header = f.read(64)
            media_type = sniff_media_type(header)
            f.seek(0)
            data = f.read()
    except Exception as e:
        return ProvenanceReport(
            asset_path=str(path.resolve()),
            engine_id="credentio_fallback",
            engine_name="Credentio Container Inspector",
            has_credentials=False,
            badge=BadgeState.INVALID,
            elapsed_seconds=time.perf_counter() - start_time,
            byte_size=file_size,
            error_message=f"I/O read failure: {e}"
        )

    has_c2pa = False
    claim_generator = None
    ai_provenance: Dict[str, Any] = {}
    assertions_found: List[Assertion] = []

    # 1. Check for standard C2PA markers and signatures
    # JPEG APP11 marker: 0xFF 0xEB containing JUMBF box
    if b"\xff\xeb" in data and (b"jumb" in data or b"JP" in data):
        has_c2pa = True

    # PNG caPt or caPI chunk
    if b"caPt" in data or b"caPI" in data or b"c2pa" in data:
        has_c2pa = True

    # MP4 uuid box (d8f03db5-4c9b-4263-8e54-11351c7b73d9) or c2pa box
    c2pa_uuid = bytes([0xd8, 0xf0, 0x3d, 0xb5, 0x4c, 0x9b, 0x42, 0x63, 0x8e, 0x54, 0x11, 0x35, 0x1c, 0x7b, 0x73, 0xd9])
    if c2pa_uuid in data or b"c2pa" in data:
        has_c2pa = True

    # WebP JUMB chunk
    if b"JUMB" in data:
        has_c2pa = True

    # Standalone .c2pa file
    if path.suffix.lower() == ".c2pa":
        has_c2pa = True

    # Extract heuristics if C2PA structure was detected
    if has_c2pa:
        # Scan for IPTC digitalSourceType markers
        if b"trainedAlgorithmicMedia" in data:
            ai_provenance["digital_source_type"] = "https://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
        elif b"compositeWithTrainedAlgorithmicMedia" in data:
            ai_provenance["digital_source_type"] = "https://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia"
        elif b"digitalCapture" in data:
            ai_provenance["digital_source_type"] = "https://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture"

        # Scan for training-mining markers
        if b"ai_generative_training" in data:
            ai_provenance["training_mining"] = {"c2pa.ai_generative_training": {"use": "detected"}}

        # Scan common claim generator strings
        for candidate in [b"Credentio", b"Adobe Photoshop", b"Photoshop", b"Imagen", b"Truepic", b"Content Authenticity"]:
            if candidate in data:
                claim_generator = candidate.decode("utf-8", errors="ignore")
                break

    elapsed = time.perf_counter() - start_time

    if not has_c2pa:
        return ProvenanceReport(
            asset_path=str(path.resolve()),
            engine_id="credentio_fallback",
            engine_name="Credentio Container Inspector",
            has_credentials=False,
            badge=BadgeState.UNSIGNED,
            elapsed_seconds=elapsed,
            byte_size=file_size,
            media_type=media_type,
            active_manifest=None,
            manifest_count=0
        )

    manifest = Manifest(
        label="urn:c2pa:container_manifest",
        title=path.stem,
        format=media_type,
        claim_generator=claim_generator or "Credentio Container Parser",
        signature=SignatureInfo(issuer="Embedded C2PA Signer"),
        assertions=assertions_found,
        ai_provenance=ai_provenance if ai_provenance else None,
        validation_statuses=[
            ValidationStatus(
                code="claimSignature.unverified_trust",
                explanation="Embedded C2PA structure detected via container inspection; native verification requires libcredentio_c.",
                severity=Severity.INFO
            )
        ]
    )

    return ProvenanceReport(
        asset_path=str(path.resolve()),
        engine_id="credentio_fallback",
        engine_name="Credentio Container Inspector",
        has_credentials=True,
        badge=BadgeState.SIGNED,
        elapsed_seconds=elapsed,
        byte_size=file_size,
        media_type=media_type,
        active_manifest=manifest,
        manifest_count=1
    )

# ============================================================================
# 4. Native Google Credentio C-ABI Engine
# ============================================================================

_native_validator_cls = None

def _get_native_validator():
    """Attempts to import or construct the native Credentio CFFI Validator."""
    global _native_validator_cls
    if _native_validator_cls is not None:
        return _native_validator_cls

    try:
        from credentio.validator import Validator
        _native_validator_cls = Validator
        return _native_validator_cls
    except ImportError:
        pass

    # Attempt dynamic load of libcredentio_c via cffi
    try:
        import cffi
        ffi = cffi.FFI()
        ffi.cdef("""
            typedef struct cr_validator cr_validator;
            cr_validator* cr_validator_create(const char* claim_signer_trust_pem, const char* tsa_trust_pem, int skip_trust_checks);
            void cr_validator_free(cr_validator* validator);
            char* cr_validate_file(cr_validator* validator, const char* file_path, const char* media_type, int* out_status);
            const char* cr_last_error(cr_validator* validator);
            double cr_last_internal_seconds(cr_validator* validator);
            void cr_string_free(char* str);
        """)

        script_dir = Path(__file__).resolve().parent
        plugin_root = script_dir.parent.parent.parent
        repo_root = plugin_root.parent.parent

        candidate_paths = [
            os.environ.get("CREDENTIO_LIB_PATH"),
            str(script_dir.parent / "lib" / "libcredentio_c.so"),
            str(script_dir.parent / "lib" / "libcredentio_c.dylib"),
            str(repo_root / "native" / "libcredentio_c.so"),
            str(repo_root / "native" / "libcredentio_c.dylib"),
            str(repo_root / "python" / "src" / "credentio" / "lib" / "libcredentio_c.so"),
            str(repo_root / "python" / "src" / "credentio" / "lib" / "libcredentio_c.dylib"),
            "/usr/local/lib/libcredentio_c.so",
            "/usr/local/lib/libcredentio_c.dylib",
            "/opt/homebrew/lib/libcredentio_c.dylib",
            str(Path.home() / ".local/lib/libcredentio_c.so"),
        ]

        lib_file = None
        for p in candidate_paths:
            if p and Path(p).is_file():
                lib_file = p
                break

        if not lib_file:
            return None

        lib = ffi.dlopen(lib_file)

        class DynamicNativeValidator:
            def __init__(self, claim_signer_trust_pem=None, tsa_trust_pem=None, skip_trust_checks=True):
                c_claim = ffi.new("char[]", claim_signer_trust_pem.encode("utf-8")) if claim_signer_trust_pem else ffi.NULL
                c_tsa = ffi.new("char[]", tsa_trust_pem.encode("utf-8")) if tsa_trust_pem else ffi.NULL
                self.ptr = lib.cr_validator_create(c_claim, c_tsa, 1 if skip_trust_checks else 0)
                if not self.ptr:
                    raise RuntimeError("Failed to initialize native cr_validator")

            def close(self):
                if self.ptr:
                    lib.cr_validator_free(self.ptr)
                    self.ptr = None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

            def validate_file(self, file_path: Path, media_type: Optional[str] = None) -> ProvenanceReport:
                out_status = ffi.new("int*")
                c_path = ffi.new("char[]", str(file_path.resolve()).encode("utf-8"))
                c_media = ffi.new("char[]", media_type.encode("utf-8")) if media_type else ffi.NULL
                t0 = time.perf_counter()
                raw_json_ptr = lib.cr_validate_file(self.ptr, c_path, c_media, out_status)
                elapsed = time.perf_counter() - t0
                core_secs = lib.cr_last_internal_seconds(self.ptr)

                status = out_status[0]
                if status == 1 or not raw_json_ptr: # CR_STATUS_NO_CREDENTIALS
                    return ProvenanceReport(
                        asset_path=str(file_path.resolve()),
                        engine_id="credentio_native_c",
                        engine_name="Google Credentio (C-ABI)",
                        has_credentials=False,
                        badge=BadgeState.UNSIGNED,
                        elapsed_seconds=elapsed,
                        core_seconds=core_secs,
                        byte_size=file_path.stat().st_size,
                        media_type=media_type
                    )

                raw_json = ffi.string(raw_json_ptr).decode("utf-8")
                lib.cr_string_free(raw_json_ptr)

                rep = parse_crjson(raw_json, media_type=media_type, elapsed_seconds=elapsed, core_seconds=core_secs, asset_path=str(file_path.resolve()))
                rep.byte_size = file_path.stat().st_size
                rep.engine_id = "credentio_native_c"
                rep.engine_name = "Google Credentio (C-ABI)"
                return rep

        _native_validator_cls = DynamicNativeValidator
        return _native_validator_cls
    except Exception:
        return None

# ============================================================================
# 5. Core Inspection Dispatcher
# ============================================================================

def inspect_file(
    file_path: Path,
    media_type: Optional[str] = None,
    claim_signer_pem: Optional[str] = None,
    tsa_pem: Optional[str] = None,
    skip_trust: bool = True
) -> ProvenanceReport:
    """Inspects a single asset using native Credentio or container fallback."""
    if not file_path.is_file():
        return ProvenanceReport(
            asset_path=str(file_path),
            engine_id="dispatcher",
            engine_name="Dispatcher",
            has_credentials=False,
            badge=BadgeState.INVALID,
            elapsed_seconds=0.0,
            error_message=f"File not found: {file_path}"
        )

    # 1. Try Native Credentio Engine
    native_cls = _get_native_validator()
    if native_cls is not None and file_path.suffix.lower() != ".json":
        try:
            with native_cls(
                claim_signer_trust_pem=claim_signer_pem,
                tsa_trust_pem=tsa_pem,
                skip_trust_checks=skip_trust
            ) as v:
                return v.validate_file(file_path, media_type=media_type)
        except Exception:
            pass

    # 2. Fall back to pure-Python Credentio container inspector
    return inspect_media_fallback(file_path)

# ============================================================================
# 6. Formatting & CLI Presentation
# ============================================================================

def format_asset_detail(report: ProvenanceReport) -> str:
    """Detailed multi-line recap for a single asset."""
    p = Path(report.asset_path)
    size_kb = report.byte_size / 1024.0
    lines = [
        "=" * 68,
        f"  C2PA Provenance Report: {p.name}",
        "=" * 68,
        f"Path:        {report.asset_path}",
        f"Size:        {size_kb:.1f} KB ({report.byte_size} bytes)",
        f"Media Type:  {report.media_type or 'unknown'}",
        f"Engine:      {report.engine_name} ({report.engine_id})",
        f"Status:      {report.badge.value.upper()}",
        f"Credentials: {'Present' if report.has_credentials else 'None'}",
    ]

    if report.active_manifest:
        m = report.active_manifest
        lines.extend([
            f"Manifest:    {m.label}",
            f"Title:       {m.title or '-'}",
            f"Generator:   {m.claim_generator or '-'}",
            f"Issuer:      {m.signature.issuer or '-' if m.signature else '-'}",
            f"Algorithm:   {m.signature.algorithm or '-' if m.signature else '-'}",
            f"Signed Time: {m.signature.time.isoformat() if (m.signature and m.signature.time) else '-'}",
            f"Assertions:  {len(m.assertions)} attached",
        ])

        if m.ai_provenance:
            ai = m.ai_provenance
            lines.append("-" * 68)
            lines.append("  AI Provenance & Training Consent:")
            if "digital_source_type" in ai:
                lines.append(f"  Source Type: {ai['digital_source_type']}")
            if "generative_model" in ai:
                model_str = f"{ai['generative_model'].get('name', '')} {ai['generative_model'].get('version', '')}".strip()
                lines.append(f"  Model:       {model_str}")
            if "prompt" in ai:
                lines.append(f"  Prompt:      \"{ai['prompt']}\"")
            if "training_mining" in ai:
                tm = ai["training_mining"]
                lines.append(f"  Training:    {tm}")

        if m.validation_statuses:
            lines.append("-" * 68)
            lines.append("  Validation Details:")
            for s in m.validation_statuses[:5]:
                expl = f": {s.explanation}" if s.explanation else ""
                lines.append(f"  [{s.severity.value.upper()}] {s.code}{expl}")

    if report.error_message:
        lines.append(f"Error:       {report.error_message}")

    lines.append(f"Elapsed:     {report.elapsed_seconds * 1000.0:.2f} ms")
    lines.append("=" * 68)
    return "\n".join(lines)

def format_batch_table(reports: List[ProvenanceReport]) -> str:
    """Formatted tabular summary for multiple assets."""
    lines = [
        "=" * 100,
        f"{'STATUS':<10} {'ASSET':<26} {'FORMAT':<14} {'GENERATOR':<22} {'AI ATTRIBUTION':<24}",
        "=" * 100,
    ]

    signed_count = 0
    unsigned_count = 0
    invalid_count = 0
    ai_count = 0

    for r in reports:
        if r.badge == BadgeState.SIGNED:
            signed_count += 1
        elif r.badge == BadgeState.UNSIGNED:
            unsigned_count += 1
        else:
            invalid_count += 1

        p = Path(r.asset_path)
        name = p.name[:24] + ".." if len(p.name) > 26 else p.name
        fmt = (r.media_type or p.suffix or "-")[:13]
        gen = "-"
        ai_str = "-"

        if r.active_manifest:
            m = r.active_manifest
            if m.claim_generator:
                gen = m.claim_generator[:20] + ".." if len(m.claim_generator) > 22 else m.claim_generator
            if m.ai_provenance:
                ai_count += 1
                dst = m.ai_provenance.get("digital_source_type", "")
                if "trainedAlgorithmicMedia" in dst:
                    ai_str = "AI Generated"
                elif "composite" in dst:
                    ai_str = "AI Composited"
                elif "digitalCapture" in dst:
                    ai_str = "Human Capture"
                elif "generative_model" in m.ai_provenance:
                    mod = m.ai_provenance["generative_model"]
                    ai_str = f"Model: {mod.get('name', 'AI')}"
                else:
                    ai_str = "AI Metadata"

        lines.append(f"{r.badge.value.upper():<10} {name:<26} {fmt:<14} {gen:<22} {ai_str:<24}")

    lines.append("=" * 100)
    total = len(reports)
    lines.extend([
        f"Total Scanned: {total}",
        f"  SIGNED:      {signed_count} ({signed_count / max(1, total) * 100:.1f}%)",
        f"  UNSIGNED:    {unsigned_count} ({unsigned_count / max(1, total) * 100:.1f}%)",
        f"  INVALID:     {invalid_count} ({invalid_count / max(1, total) * 100:.1f}%)",
        f"  AI ATTR:     {ai_count} ({ai_count / max(1, total) * 100:.1f}%)",
        "=" * 100,
    ])
    return "\n".join(lines)

def to_dict_report(report: ProvenanceReport) -> Dict[str, Any]:
    """Converts a ProvenanceReport to JSON-serializable dictionary."""
    m = report.active_manifest
    return {
        "asset_path": report.asset_path,
        "byte_size": report.byte_size,
        "media_type": report.media_type,
        "engine_id": report.engine_id,
        "engine_name": report.engine_name,
        "has_credentials": report.has_credentials,
        "badge": report.badge.value,
        "spec_version": report.spec_version,
        "elapsed_seconds": report.elapsed_seconds,
        "core_seconds": report.core_seconds,
        "error_message": report.error_message,
        "active_manifest": {
            "label": m.label,
            "title": m.title,
            "claim_generator": m.claim_generator,
            "format": m.format,
            "signature": {
                "issuer": m.signature.issuer,
                "algorithm": m.signature.algorithm,
                "time": m.signature.time.isoformat() if m.signature and m.signature.time else None,
                "cert_serial_number": m.signature.cert_chain_summary,
            } if m.signature else None,
            "ai_provenance": m.ai_provenance,
            "assertions_count": len(m.assertions),
            "validation_statuses_count": len(m.validation_statuses),
            "validation_statuses": [
                {
                    "code": s.code,
                    "explanation": s.explanation,
                    "severity": s.severity.value
                } for s in m.validation_statuses
            ]
        } if m else None
    }

# ============================================================================
# 7. Main Entry Point
# ============================================================================

def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="inspect_c2pa.py",
        description="Google Credentio C2PA Content Credentials Inspector & Batch Auditor"
    )
    parser.add_argument("targets", nargs="*", help="File paths, glob patterns, or directories to inspect")
    parser.add_argument("--dir", "-d", type=Path, default=None, help="Directory to inspect")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively scan subdirectories")
    parser.add_argument("--json", action="store_true", help="Output machine-readable structured JSON")
    parser.add_argument("--summary-only", action="store_true", help="Output aggregate metrics table only")
    parser.add_argument("--filter", choices=["all", "signed", "unsigned", "invalid", "ai-only"], default="all", help="Filter output by status")
    parser.add_argument("--media-type", "-m", type=str, default=None, help="Force explicit media type")
    parser.add_argument("--claim-signer-trust", type=Path, default=None, help="Path to claim signer trust PEM")
    parser.add_argument("--tsa-trust", type=Path, default=None, help="Path to TSA trust PEM")
    parser.add_argument("--skip-trust-checks", action="store_true", default=True, help="Skip trust anchor checks")

    parsed = parser.parse_args(args)

    # 1. Collect target files
    candidate_paths: List[Path] = []

    # Positional targets (paths or globs)
    for t in parsed.targets:
        if any(c in t for c in ("*", "?", "[")):
            for match in glob.glob(t, recursive=parsed.recursive):
                p = Path(match)
                if p.is_file():
                    candidate_paths.append(p)
        else:
            p = Path(t)
            if p.is_file():
                candidate_paths.append(p)
            elif p.is_dir():
                pattern = "**/*" if parsed.recursive else "*"
                for child in p.glob(pattern):
                    if child.is_file():
                        candidate_paths.append(child)

    # Directory option
    if parsed.dir:
        if not parsed.dir.is_dir():
            print(f"Error: Directory not found: {parsed.dir}", file=sys.stderr)
            return 3
        pattern = "**/*" if parsed.recursive else "*"
        for child in parsed.dir.glob(pattern):
            if child.is_file():
                candidate_paths.append(child)

    # Deduplicate while preserving order
    seen = set()
    files_to_inspect = []
    for p in candidate_paths:
        resolved = str(p.resolve())
        if resolved not in seen:
            seen.add(resolved)
            files_to_inspect.append(p)

    if not files_to_inspect:
        if not parsed.targets and not parsed.dir:
            parser.print_help()
            return 0
        print("Error: No matching files found to inspect.", file=sys.stderr)
        return 3

    # 2. Read trust anchor files if provided
    claim_pem = parsed.claim_signer_trust.read_text("utf-8") if parsed.claim_signer_trust else None
    tsa_pem = parsed.tsa_trust.read_text("utf-8") if parsed.tsa_trust else None
    skip_trust = False if (claim_pem or tsa_pem) else parsed.skip_trust_checks

    # 3. Perform inspections
    reports: List[ProvenanceReport] = []
    for file_path in files_to_inspect:
        rep = inspect_file(
            file_path=file_path,
            media_type=parsed.media_type,
            claim_signer_pem=claim_pem,
            tsa_pem=tsa_pem,
            skip_trust=skip_trust
        )
        reports.append(rep)

    # 4. Filter results if requested
    filtered_reports = []
    for r in reports:
        if parsed.filter == "signed" and r.badge != BadgeState.SIGNED:
            continue
        if parsed.filter == "unsigned" and r.badge != BadgeState.UNSIGNED:
            continue
        if parsed.filter == "invalid" and r.badge != BadgeState.INVALID:
            continue
        if parsed.filter == "ai-only":
            is_ai = bool(r.active_manifest and r.active_manifest.ai_provenance)
            if not is_ai:
                continue
        filtered_reports.append(r)

    # 5. Emit formatted output
    if parsed.json:
        summary_stats = {
            "total_scanned": len(reports),
            "reported_count": len(filtered_reports),
            "signed_count": sum(1 for r in reports if r.badge == BadgeState.SIGNED),
            "unsigned_count": sum(1 for r in reports if r.badge == BadgeState.UNSIGNED),
            "invalid_count": sum(1 for r in reports if r.badge == BadgeState.INVALID),
            "ai_attributed_count": sum(1 for r in reports if (r.active_manifest and r.active_manifest.ai_provenance)),
        }
        output_payload = {
            "summary": summary_stats,
            "assets": [to_dict_report(r) for r in filtered_reports]
        }
        print(json.dumps(output_payload, indent=2))
    elif len(reports) == 1 and not parsed.summary_only and parsed.filter == "all":
        print(format_asset_detail(reports[0]))
    else:
        print(format_batch_table(filtered_reports))

    # 6. Exit code semantics
    if any(r.badge == BadgeState.INVALID for r in reports):
        return 2
    if parsed.filter == "signed" and any(r.badge == BadgeState.UNSIGNED for r in reports):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
