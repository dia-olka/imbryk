import type { WorldLedger } from './world-ledger.types.js';

export function serializeLedgerToSynopsis(ledger: WorldLedger): string {
  const sections: string[] = [];

  sections.push(`EPOCH: ${ledger.epoch}`);
  if (ledger.synopsis) {
    sections.push(ledger.synopsis);
  }

  sections.push(serializeGeopolitics(ledger));
  sections.push(serializeEconomics(ledger));
  sections.push(serializeTechnology(ledger));
  sections.push(serializeCulture(ledger));
  sections.push(serializeMilitary(ledger));
  sections.push(serializeEnvironment(ledger));
  sections.push(serializeHistory(ledger));

  return sections.filter(Boolean).join('\n\n');
}

function serializeGeopolitics(ledger: WorldLedger): string {
  const { nations, alliances, conflicts } = ledger.geopolitics;
  const lines: string[] = ['--- GEOPOLITICS ---'];

  if (nations.length > 0) {
    lines.push('Nations:');
    for (const n of nations) {
      lines.push(
        `- ${n.name} (${n.governmentType}, leader: ${n.leader}, stability: ${n.stability}/100): ${n.description}`
      );
    }
  }

  if (alliances.length > 0) {
    lines.push('Alliances:');
    for (const a of alliances) {
      lines.push(`- ${a.name} [${a.members.join(', ')}]: ${a.purpose}`);
    }
  }

  if (conflicts.length > 0) {
    lines.push('Conflicts:');
    for (const c of conflicts) {
      lines.push(
        `- ${c.name} (${c.status}) [${c.parties.join(' vs ')}]: ${c.description}`
      );
    }
  }

  return lines.join('\n');
}

function serializeEconomics(ledger: WorldLedger): string {
  const { currencies, tradingBlocs, scarcities, globalGdpTrend } =
    ledger.economics;
  const lines: string[] = ['--- ECONOMICS ---'];

  if (currencies.length > 0) {
    lines.push('Currencies:');
    for (const c of currencies) {
      lines.push(
        `- ${c.name} (issuer: ${c.issuingEntity}, strength: ${c.strength}/100): ${c.description}`
      );
    }
  }

  if (tradingBlocs.length > 0) {
    lines.push('Trading Blocs:');
    for (const t of tradingBlocs) {
      lines.push(`- ${t.name} [${t.members.join(', ')}]: ${t.focus}`);
    }
  }

  if (scarcities.length > 0) {
    lines.push('Scarcities:');
    for (const s of scarcities) {
      lines.push(
        `- ${s.resource} (${s.severity}, regions: ${s.affectedRegions.join(', ')}): ${s.description}`
      );
    }
  }

  if (globalGdpTrend) {
    lines.push(`GDP Trend: ${globalGdpTrend}`);
  }

  return lines.join('\n');
}

function serializeTechnology(ledger: WorldLedger): string {
  const { ai, energy, biotech, other } = ledger.technology;
  const lines: string[] = ['--- TECHNOLOGY ---'];

  for (const domain of [ai, energy, biotech, ...other]) {
    lines.push(
      `${domain.name} (${domain.maturityLevel}): ${domain.description}`
    );
    if (domain.keyPlayers.length > 0) {
      lines.push(`  Key players: ${domain.keyPlayers.join('; ')}`);
    }
  }

  return lines.join('\n');
}

function serializeCulture(ledger: WorldLedger): string {
  const { dominantNarratives, movements, mediaLandscape } = ledger.culture;
  const lines: string[] = ['--- CULTURE ---'];

  if (dominantNarratives.length > 0) {
    lines.push('Dominant Narratives:');
    for (const n of dominantNarratives) {
      lines.push(`- ${n}`);
    }
  }

  if (movements.length > 0) {
    lines.push('Movements:');
    for (const m of movements) {
      lines.push(`- ${m.name} (${m.reach}): ${m.description}`);
    }
  }

  if (mediaLandscape) {
    lines.push(`Media Landscape: ${mediaLandscape}`);
  }

  return lines.join('\n');
}

function serializeMilitary(ledger: WorldLedger): string {
  const { forces, armsRaces, doctrineShifts } = ledger.military;
  const lines: string[] = ['--- MILITARY ---'];

  if (forces.length > 0) {
    lines.push('Forces:');
    for (const f of forces) {
      const nuclear = f.nuclearCapable ? ', nuclear-capable' : '';
      lines.push(
        `- ${f.entity} (strength: ${f.conventionalStrength}/100${nuclear}): ${f.specialCapabilities.join(', ')}`
      );
    }
  }

  if (armsRaces.length > 0) {
    lines.push('Arms Races:');
    for (const r of armsRaces) {
      lines.push(`- ${r}`);
    }
  }

  if (doctrineShifts.length > 0) {
    lines.push('Doctrine Shifts:');
    for (const d of doctrineShifts) {
      lines.push(`- ${d}`);
    }
  }

  return lines.join('\n');
}

function serializeEnvironment(ledger: WorldLedger): string {
  const { globalTemperatureAnomaly, crises, mitigationEfforts } =
    ledger.environment;
  const lines: string[] = ['--- ENVIRONMENT ---'];

  lines.push(`Global Temperature Anomaly: +${globalTemperatureAnomaly}\u00B0C`);

  if (crises.length > 0) {
    lines.push('Crises:');
    for (const c of crises) {
      lines.push(
        `- ${c.name} (${c.severity}, regions: ${c.affectedRegions.join(', ')}): ${c.description}`
      );
    }
  }

  if (mitigationEfforts.length > 0) {
    lines.push('Mitigation Efforts:');
    for (const e of mitigationEfforts) {
      lines.push(`- ${e}`);
    }
  }

  return lines.join('\n');
}

function serializeHistory(ledger: WorldLedger): string {
  const events = ledger.history.slice(-10);
  if (events.length === 0) return '';

  const lines: string[] = ['--- RECENT HISTORY ---'];
  for (const e of events) {
    lines.push(`[${e.date}] ${e.headline}: ${e.description} (Impact: ${e.impact})`);
  }

  return lines.join('\n');
}
