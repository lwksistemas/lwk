# ⌨️ Consertar Teclas Específicas - Mapeamento Errado

## 🚨 PROBLEMA

Teclado está em português, mas teclas específicas estão erradas (barra, dois pontos, etc).

## ✅ SOLUÇÃO 1: Testar Variantes do Português

```bash
# Tentar variante padrão
setxkbmap -layout br

# Tentar variante ABNT2
setxkbmap -model abnt2 -layout br -variant abnt2

# Tentar variante nodeadkeys (sem acentos mortos)
setxkbmap -layout br -variant nodeadkeys

# Tentar variante nativo
setxkbmap -layout br -variant nativo
```

**Teste cada um e veja qual funciona!**

## ✅ SOLUÇÃO 2: Remapear Teclas Manualmente

Se uma tecla específica está errada, você pode remapeá-la:

```bash
# Ver código da tecla
xev
# (Pressione a tecla e veja o keycode)

# Remapear tecla (exemplo: keycode 61 para barra)
xmodmap -e "keycode 61 = slash question"
```

## ✅ SOLUÇÃO 3: Usar xmodmap para Corrigir

Crie um arquivo de configuração:

```bash
nano ~/.Xmodmap
```

**Adicione (exemplo para corrigir barra e dois pontos):**
```
! Corrigir barra
keycode 61 = slash question

! Corrigir dois pontos
keycode 47 = semicolon colon

! Corrigir interrogação
keycode 61 = slash question
```

**Aplique:**
```bash
xmodmap ~/.Xmodmap

# Tornar permanente
echo 'xmodmap ~/.Xmodmap' >> ~/.bashrc
```

## ✅ SOLUÇÃO 4: Verificar Modelo do Teclado

```bash
# Ver configuração atual
setxkbmap -query

# Tentar diferentes modelos
setxkbmap -model pc105 -layout br
setxkbmap -model abnt2 -layout br
setxkbmap -model pc104 -layout br
```

## 🧪 TESTE RÁPIDO

**Execute estes comandos um por um e teste após cada:**

```bash
# Comando 1
setxkbmap -layout br -variant abnt2

# Comando 2
setxkbmap -model abnt2 -layout br

# Comando 3
setxkbmap -layout br -variant nodeadkeys

# Comando 4
setxkbmap -model pc105 -layout br
```

## 🔍 IDENTIFICAR O PROBLEMA

**Descubra qual tecla está errada:**

```bash
# Abrir ferramenta de teste
xev
```

1. Pressione a tecla que está errada
2. Veja o `keycode` que aparece
3. Anote o número

**Exemplo de saída:**
```
KeyPress event, keycode 61 (keysym 0x2f, slash)
```

## 💡 SOLUÇÃO TEMPORÁRIA

**Enquanto não conserta, use estas alternativas:**

### Para barra `/`:
- Copie daqui: `/`
- Ou use: Alt + 47 (no teclado numérico)

### Para dois pontos `:`:
- Copie daqui: `:`
- Ou use: Alt + 58 (no teclado numérico)

### Para interrogação `?`:
- Copie daqui: `?`
- Ou use: Alt + 63 (no teclado numérico)

## 🎯 COMANDO MÁGICO

**Tente este comando que geralmente resolve:**

```bash
setxkbmap -model abnt2 -layout br -variant abnt2 -option ""
```

## 🔧 RESETAR TUDO

Se nada funcionar, resete completamente:

```bash
# Remover configurações personalizadas
rm ~/.Xmodmap
rm ~/.xmodmaprc

# Resetar para padrão
setxkbmap -layout br

# Reiniciar X
sudo systemctl restart gdm
# ou
sudo systemctl restart lightdm
```

## 📋 CHECKLIST

Teste cada comando e marque o que funciona:

- [ ] `setxkbmap -layout br -variant abnt2`
- [ ] `setxkbmap -model abnt2 -layout br`
- [ ] `setxkbmap -layout br -variant nodeadkeys`
- [ ] `setxkbmap -model pc105 -layout br`
- [ ] `setxkbmap -model abnt2 -layout br -variant abnt2 -option ""`

## 🆘 SE NADA FUNCIONAR

Pode ser problema de hardware. Tente:

1. **Teclado externo USB** - Para confirmar se é hardware
2. **Teclado virtual** - `onboard` ou `florence`
3. **Atualizar drivers** - `sudo apt update && sudo apt upgrade`

---

**Teste os comandos acima e me diga qual funcionou!** ⌨️
