# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/i18n.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The texts the command line and the panel contract show, in the eight languages (pt is European Portuguese).

Every key has all eight languages; a test checks it. Keys that start with `label.` are also exported in the panel contract.
"""
from __future__ import annotations

from .settings import LANGUAGES

_ORDER = LANGUAGES  # en, es, de, fr, it, ja, zh, pt


def _row(*texts: str) -> dict[str, str]:
    assert len(texts) == len(_ORDER)
    return dict(zip(_ORDER, texts, strict=True))


MESSAGES: dict[str, dict[str, str]] = {
    "label.title": _row("Developer node", "Nodo de desarrollo", "Entwicklungsknoten", "Nœud de développement", "Nodo di sviluppo",
                        "開発ノード", "开发节点", "Nó de desenvolvimento"),
    "label.switches": _row("Switches", "Interruptores", "Schalter", "Interrupteurs", "Interruttori", "スイッチ", "开关", "Interruptores"),
    "label.on": _row("on", "activado", "an", "activé", "attivo", "オン", "开", "ativado"),
    "label.off": _row("off", "apagado", "aus", "désactivé", "spento", "オフ", "关", "desativado"),
    "label.queue": _row("Queue", "Cola", "Warteschlange", "File d'attente", "Coda", "キュー", "队列", "Fila"),
    "label.cases": _row("Cases", "Casos", "Fälle", "Cas", "Casi", "ケース", "案例", "Casos"),
    "label.awaiting-review": _row("Waiting for review", "Esperando revisión", "Wartet auf Prüfung", "En attente de revue",
                                  "In attesa di revisione", "レビュー待ち", "等待审核", "A aguardar revisão"),
    "label.awaiting_approval": _row("Approvals waiting to be used", "Aprobaciones pendientes de usar", "Freigaben, die noch nicht genutzt wurden",
                                    "Approbations en attente d'utilisation", "Approvazioni in attesa di essere usate",
                                    "未使用の承認", "尚未使用的批准", "Aprovações por utilizar"),
    "label.outcomes": _row("Recorded runs", "Ejecuciones registradas", "Aufgezeichnete Läufe", "Exécutions enregistrées",
                           "Esecuzioni registrate", "記録された実行", "已记录的运行", "Execuções registadas"),
    "label.journal": _row("Journal", "Diario", "Journal", "Journal", "Registro", "ジャーナル", "日志", "Diário"),
    "label.health": _row("Health", "Salud", "Zustand", "Santé", "Stato di salute", "状態", "健康状况", "Estado de saúde"),
    "label.store_ok": _row("Database intact", "Base de datos íntegra", "Datenbank intakt", "Base de données intacte",
                           "Database integro", "データベースは正常", "数据库完好", "Base de dados íntegra"),
    "label.cache": _row("Checkout cache", "Caché de checkouts", "Checkout-Cache", "Cache des checkouts", "Cache dei checkout",
                        "チェックアウトのキャッシュ", "检出缓存", "Cache de checkouts"),
    "label.over_limit": _row("Over its limit", "Por encima del límite", "Über dem Limit", "Au-dessus de la limite", "Oltre il limite",
                             "上限超過", "超过上限", "Acima do limite"),
    "label.ci_report": _row("Last ecosystem CI report", "Último informe de CI del ecosistema", "Letzter CI-Bericht des Ökosystems",
                            "Dernier rapport CI de l'écosystème", "Ultimo rapporto CI dell'ecosistema", "最新のエコシステム CI レポート",
                            "最近的生态系统 CI 报告", "Último relatório de CI do ecossistema"),
    "label.none": _row("none", "ninguno", "keiner", "aucun", "nessuno", "なし", "无", "nenhum"),
    "msg.ingested": _row("Case {case} stored; it waits for a person to review it.", "Caso {case} guardado; espera a que una persona lo revise.",
                         "Fall {case} gespeichert; er wartet auf die Prüfung durch einen Menschen.",
                         "Cas {case} enregistré ; il attend la revue d'une personne.",
                         "Caso {case} salvato; attende la revisione di una persona.", "ケース {case} を保存しました。担当者のレビュー待ちです。",
                         "案例 {case} 已保存，等待人工审核。", "Caso {case} guardado; aguarda a revisão de uma pessoa."),
    "msg.duplicate": _row("Case {case} was already stored; nothing changed.", "El caso {case} ya estaba guardado; no cambió nada.",
                          "Fall {case} war schon gespeichert; nichts hat sich geändert.", "Le cas {case} était déjà enregistré ; rien n'a changé.",
                          "Il caso {case} era già salvato; non è cambiato nulla.", "ケース {case} は保存済みです。変更はありません。",
                          "案例 {case} 已存在，没有任何改动。", "O caso {case} já estava guardado; nada mudou."),
    "msg.bundle_ok": _row("The bundle is valid and its checksum matches ({steps} reproduction steps).",
                          "El paquete es válido y su suma de comprobación coincide ({steps} pasos de reproducción).",
                          "Das Paket ist gültig und die Prüfsumme stimmt ({steps} Reproduktionsschritte).",
                          "Le paquet est valide et sa somme de contrôle correspond ({steps} étapes de reproduction).",
                          "Il pacchetto è valido e il checksum coincide ({steps} passi di riproduzione).",
                          "バンドルは有効でチェックサムも一致しています（再現手順 {steps} 件）。",
                          "数据包有效，校验和一致（{steps} 个复现步骤）。",
                          "O pacote é válido e a soma de verificação coincide ({steps} passos de reprodução)."),
    "msg.approved": _row("Approved: {what}.", "Aprobado: {what}.", "Freigegeben: {what}.", "Approuvé : {what}.", "Approvato: {what}.",
                         "承認しました: {what}。", "已批准：{what}。", "Aprovado: {what}."),
    "msg.run_outcome": _row("Run {phase}: {outcome}.", "Ejecución {phase}: {outcome}.", "Lauf {phase}: {outcome}.",
                            "Exécution {phase} : {outcome}.", "Esecuzione {phase}: {outcome}.", "実行 {phase}: {outcome}。",
                            "运行 {phase}：{outcome}。", "Execução {phase}: {outcome}."),
    "msg.checkout_ready": _row("Checkout ready: {path} at {sha}.", "Checkout listo: {path} en {sha}.", "Checkout bereit: {path} bei {sha}.",
                               "Checkout prêt : {path} à {sha}.", "Checkout pronto: {path} a {sha}.", "チェックアウト完了: {path}（{sha}）。",
                               "检出完成：{path}，提交 {sha}。", "Checkout pronto: {path} em {sha}."),
    "msg.pruned": _row("{count} worktree(s) removed to fit the cache limit.", "{count} worktree(s) eliminados para respetar el límite de la caché.",
                       "{count} Worktree(s) entfernt, damit der Cache ins Limit passt.",
                       "{count} worktree(s) supprimé(s) pour respecter la limite du cache.",
                       "{count} worktree rimossi per rispettare il limite della cache.", "キャッシュの上限に収めるため worktree を {count} 件削除しました。",
                       "已删除 {count} 个 worktree 以满足缓存上限。", "{count} worktree(s) removido(s) para respeitar o limite da cache."),
    "msg.cache_over": _row("The cache is still over its limit and has no worktree left to remove.",
                           "La caché sigue por encima del límite y ya no quedan worktrees que eliminar.",
                           "Der Cache liegt weiter über dem Limit und hat keine Worktrees mehr zum Entfernen.",
                           "Le cache dépasse encore la limite et n'a plus de worktree à supprimer.",
                           "La cache supera ancora il limite e non ha più worktree da rimuovere.",
                           "キャッシュは依然として上限を超えており、削除できる worktree がありません。",
                           "缓存仍超过上限，且没有可删除的 worktree。",
                           "A cache continua acima do limite e já não tem worktrees para remover."),
    "msg.ci_done": _row("Ecosystem CI: {passed} passed, {failed} failed, {errors} with errors, {skipped} skipped.",
                        "CI del ecosistema: {passed} correctos, {failed} fallidos, {errors} con error, {skipped} omitidos.",
                        "Ökosystem-CI: {passed} bestanden, {failed} fehlgeschlagen, {errors} mit Fehler, {skipped} übersprungen.",
                        "CI de l'écosystème : {passed} réussis, {failed} échoués, {errors} en erreur, {skipped} ignorés.",
                        "CI dell'ecosistema: {passed} superati, {failed} falliti, {errors} con errore, {skipped} saltati.",
                        "エコシステム CI: 成功 {passed}、失敗 {failed}、エラー {errors}、スキップ {skipped}。",
                        "生态系统 CI：通过 {passed}，失败 {failed}，出错 {errors}，跳过 {skipped}。",
                        "CI do ecossistema: {passed} aprovados, {failed} falhados, {errors} com erro, {skipped} ignorados."),
    "label.ci_full_report": _row("Last complete ecosystem CI report", "Último informe de CI completo del ecosistema",
                                 "Letzter vollständiger CI-Bericht des Ökosystems", "Dernier rapport CI complet de l'écosystème",
                                 "Ultimo rapporto CI completo dell'ecosistema", "最新のエコシステム CI フルレポート", "最近的生态系统完整 CI 报告",
                                 "Último relatório de CI completo do ecossistema"),
    "label.status_pass": _row("passed", "correcto", "bestanden", "réussi", "superato", "成功", "通过", "aprovado"),
    "label.status_fail": _row("failed", "fallido", "fehlgeschlagen", "échoué", "fallito", "失敗", "失败", "falhado"),
    "label.status_timeout": _row("timed out", "tiempo agotado", "Zeitlimit überschritten", "délai dépassé", "tempo scaduto", "タイムアウト",
                                 "超时", "tempo esgotado"),
    "label.status_skipped": _row("skipped", "omitido", "übersprungen", "ignoré", "saltato", "スキップ", "已跳过", "ignorado"),
    "msg.full_line": _row("{repo}: {status} in {seconds} s ({command})", "{repo}: {status} en {seconds} s ({command})",
                          "{repo}: {status} nach {seconds} s ({command})", "{repo} : {status} en {seconds} s ({command})",
                          "{repo}: {status} in {seconds} s ({command})", "{repo}: {status}（{seconds} 秒、{command}）",
                          "{repo}：{status}，用时 {seconds} 秒（{command}）", "{repo}: {status} em {seconds} s ({command})"),
    "msg.full_done": _row("Complete ecosystem CI: {passed} passed, {failed} failed, {timeouts} timed out, {skipped} skipped.",
                          "CI completo del ecosistema: {passed} correctos, {failed} fallidos, {timeouts} con tiempo agotado, {skipped} omitidos.",
                          "Vollständige Ökosystem-CI: {passed} bestanden, {failed} fehlgeschlagen, {timeouts} Zeitlimit überschritten, {skipped} übersprungen.",
                          "CI complète de l'écosystème : {passed} réussis, {failed} échoués, {timeouts} au délai dépassé, {skipped} ignorés.",
                          "CI completa dell'ecosistema: {passed} superati, {failed} falliti, {timeouts} a tempo scaduto, {skipped} saltati.",
                          "エコシステム CI（完全）: 成功 {passed}、失敗 {failed}、タイムアウト {timeouts}、スキップ {skipped}。",
                          "完整生态系统 CI：通过 {passed}，失败 {failed}，超时 {timeouts}，跳过 {skipped}。",
                          "CI completo do ecossistema: {passed} aprovados, {failed} falhados, {timeouts} com tempo esgotado, {skipped} ignorados."),
    "msg.full_aborted": _row("The run was cut short: {reason}.", "La ejecución se cortó: {reason}.", "Der Lauf wurde vorzeitig beendet: {reason}.",
                             "L'exécution a été interrompue : {reason}.", "L'esecuzione è stata interrotta: {reason}.",
                             "実行は途中で打ち切られました: {reason}。", "运行被提前终止：{reason}。", "A execução foi interrompida: {reason}."),
    "msg.full_plan_hint": _row("Review the commands above, then approve this exact plan with the same --exclude options.",
                               "Revise los comandos de arriba y apruebe este plan exacto con las mismas opciones --exclude.",
                               "Prüfen Sie die Befehle oben und geben Sie genau diesen Plan mit denselben --exclude-Optionen frei.",
                               "Relisez les commandes ci-dessus, puis approuvez ce plan exact avec les mêmes options --exclude.",
                               "Controlli i comandi qui sopra, poi approvi questo piano esatto con le stesse opzioni --exclude.",
                               "上のコマンドを確認し、同じ --exclude オプションでこのプランを正確に承認してください。",
                               "请检查上面的命令，然后使用相同的 --exclude 选项批准这份确切的计划。",
                               "Reveja os comandos acima e aprove este plano exato com as mesmas opções --exclude."),
    "msg.refused": _row("Refused: {reason}", "Rechazado: {reason}", "Abgelehnt: {reason}", "Refusé : {reason}", "Rifiutato: {reason}",
                        "拒否しました: {reason}", "已拒绝：{reason}", "Recusado: {reason}"),
    "msg.no_cases": _row("There are no cases.", "No hay casos.", "Es gibt keine Fälle.", "Il n'y a aucun cas.", "Non ci sono casi.",
                         "ケースはありません。", "没有案例。", "Não há casos."),
    "msg.config_ok": _row("The configuration is valid; closed switches: {closed}.", "La configuración es válida; interruptores apagados: {closed}.",
                          "Die Konfiguration ist gültig; ausgeschaltete Schalter: {closed}.",
                          "La configuration est valide ; interrupteurs désactivés : {closed}.",
                          "La configurazione è valida; interruttori spenti: {closed}.", "設定は有効です。オフのスイッチ: {closed}。",
                          "配置有效；已关闭的开关：{closed}。", "A configuração é válida; interruptores desativados: {closed}."),
}


def t(key: str, language: str = "en", **values: object) -> str:
    """The text of `key` in `language`, with the `{name}` fields filled. An unknown key or language falls back to English or the key."""
    row = MESSAGES.get(key)
    if row is None:
        return key
    text = row.get(language) or row["en"]
    return text.format(**values) if values else text


def labels(language: str) -> dict[str, str]:
    """The `label.*` texts in one language, keyed without the prefix."""
    return {key[len("label."):]: row.get(language) or row["en"] for key, row in MESSAGES.items() if key.startswith("label.")}
