# ⌨️ Consertar Teclado do Notebook - Linux

## 🚨 Problema

Teclas como `/` (barra), `:` (dois pontos) e outras estão erradas.

**Causa:** Layout do teclado está configurado como inglês (US) em vez de português (BR).

## ✅ SOLUÇÃO RÁPIDA

### Opção 1: Via Interface Gráfica (Mais Fácil)

#### Ubuntu/Debian:
1. Abra **Configurações** (Settings)
2. Vá em **Região e Idioma** (Region & Language)
3. Clique em **Fontes de Entrada** (Input Sources)
4. Remova o teclado inglês (US)
5. Adicione **Português (Brasil)**
6. Reinicie ou faça logout/login

#### Fedora/GNOME:
1. Abra **Configurações**
2. Vá em **Teclado** (Keyboard)
3. Clique em **Fontes de Entrada**
4. Adicione **Português (Brasil)**
5. Remova o inglês (US)

### Opção 2: Via Terminal (Mais Rápido)

```bash
# Configurar teclado para português brasileiro
setxkbmap -model abnt2 -layout br -variant abnt2

# Tornar permanente (adicionar ao .bashrc)
echo 'setxkbmap -model abnt2 -layout br -variant abnt2' >> ~/.bashrc
```

### Opção 3: Configuração do Sistema

```bash
# Editar configuração do teclado
sudo nano /etc/default/keyboard
```

**Altere para:**
```
XKBMODEL="abnt2"
XKBLAYOUT="br"
XKBVARIANT="abnt2"
XKBOPTIONS=""
```

**Salve e aplique:**
```bash
sudo dpkg-reconfigure keyboard-configuration
sudo service keyboard-setup restart
```

## 🧪 TESTAR

Após aplicar, teste estas teclas:

```
/ (barra) - Deve funcionar
: (dois pontos) - Shift + ;
? (interrogação) - Shift + /
" (aspas) - Shift + '
ç (cedilha) - Deve funcionar
~ (til) - Deve funcionar
```

## 🔧 SOLUÇÃO TEMPORÁRIA (Enquanto não conserta)

Se precisar digitar caracteres específicos agora:

**Barra (/):**
- Teclado US: Tecla `/` (ao lado do Shift direito)
- Teclado BR: Tecla `/` (ao lado do Shift direito)

**Dois pontos (:):**
- Teclado US: Shift + `;`
- Teclado BR: Shift + `;`

**Interrogação (?):**
- Teclado US: Shift + `/`
- Teclado BR: Shift + `/`

## 📋 MAPEAMENTO DE TECLAS

### Teclado US vs BR

| Tecla | US | BR |
|-------|----|----|
| `/` | `/` | `/` |
| `:` | Shift + `;` | Shift + `;` |
| `?` | Shift + `/` | Shift + `/` |
| `"` | Shift + `'` | Shift + `'` |
| `ç` | Não tem | `ç` |
| `~` | Shift + `` ` `` | `~` |

## 🎯 COMANDO RÁPIDO

**Execute este comando agora:**

```bash
setxkbmap -model abnt2 -layout br -variant abnt2
```

Isso vai consertar imediatamente! ✅

## 🔄 REINICIAR CONFIGURAÇÃO

Se nada funcionar:

```bash
# Resetar configuração do X
sudo dpkg-reconfigure keyboard-configuration

# Reiniciar serviço
sudo systemctl restart keyboard-setup.service

# Ou reiniciar o computador
sudo reboot
```

## 💡 DICA

Para alternar entre layouts rapidamente:

```bash
# Português BR
setxkbmap br

# Inglês US
setxkbmap us
```

---

**Execute o comando rápido agora e teste!** ⌨️✨
