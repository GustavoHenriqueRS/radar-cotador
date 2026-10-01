import { useCallback, useEffect, useRef, useState } from "react";
import { get } from "./api";

/** Busca um recurso da API; `intervalo` (ms) refaz a busca enquanto `continuar(dados)` for verdadeiro. */
export function useApi<T>(caminho: string | null, intervalo?: number, continuar?: (dados: T) => boolean) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const continuarRef = useRef(continuar);
  continuarRef.current = continuar;
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const montado = useRef(true);

  // O acompanhamento recomeça a cada busca, inclusive a disparada por uma ação (reprocessar, coletar):
  // se a condição voltou a valer, a página volta a se atualizar sozinha.
  const recarregar = useCallback(async (): Promise<T | undefined> => {
    if (!caminho) return;
    clearTimeout(timer.current);
    try {
      const d = await get<T>(caminho);
      if (!montado.current) return d;
      setDados(d);
      setErro(null);
      if (intervalo && (!continuarRef.current || continuarRef.current(d))) {
        timer.current = setTimeout(recarregar, intervalo);
      }
      return d;
    } catch (e) {
      if (montado.current) setErro((e as Error).message);
    } finally {
      if (montado.current) setCarregando(false);
    }
  }, [caminho, intervalo]);

  useEffect(() => {
    montado.current = true;
    setCarregando(true);
    recarregar();
    return () => {
      montado.current = false;
      clearTimeout(timer.current);
    };
  }, [recarregar]);

  return { dados, erro, carregando, recarregar };
}
