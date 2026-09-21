"""
Módulo de logging do Google Flow Engine
Garante que todas as mensagens informativas e de progresso sejam enviadas para sys.stderr,
mantendo o sys.stdout estritamente limpo para payloads JSON consumidos por Agentes de IA.
"""

import sys

def log(msg: str):
    """Envia mensagens de status para sys.stderr preservando stdout para envelopes JSON."""
    try:
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr.buffer.write((str(msg) + "\n").encode('utf-8', errors='replace'))
            sys.stderr.buffer.flush()
        else:
            print(msg, file=sys.stderr, flush=True)
    except Exception:
        try:
            print(str(msg).encode('ascii', errors='replace').decode('ascii'), file=sys.stderr, flush=True)
        except Exception:
            pass
