import asyncio

def test_google_knowledge():
    print("\n=== Testando integração com Google Knowledge ===\n")
    
    from server.integrations.google_knowledge import fetch_doc_text, fetch_sheet_catalog, build_context_for_intent
    from server.config import GOOGLE_DOC_ID, GOOGLE_SHEET_ID

    # Testa busca no documento
    print("1. Buscando informações do Google Doc...")
    doc_text = fetch_doc_text(GOOGLE_DOC_ID)
    if doc_text:
        print(f"✓ Documento encontrado! Primeiros 200 caracteres:\n{doc_text[:200]}...")
    else:
        print("✗ Não foi possível ler o documento. Verifique GOOGLE_DOC_ID e as credenciais.")
    
    print("\n2. Buscando informações da planilha...")
    catalog = fetch_sheet_catalog(GOOGLE_SHEET_ID)
    if catalog["items"]:
        print(f"✓ Planilha encontrada! Exemplo de items:\n{catalog['preview'][:200]}...")
    else:
        print("✗ Não foi possível ler a planilha. Verifique GOOGLE_SHEET_ID e as credenciais.")
    
    print("\n3. Testando contexto para diferentes intenções...")
    for intent in ["Catálogo", "Atendimento", "Pedidos"]:
        ctx = build_context_for_intent(intent)
        print(f"\nContexto para {intent}:")
        for k, v in ctx.items():
            print(f"- {k}: {len(str(v))} caracteres")

if __name__ == "__main__":
    asyncio.run(test_google_knowledge())