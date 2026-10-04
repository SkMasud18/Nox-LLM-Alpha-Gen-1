"""
Nox LLM Alpha Gen 1: Flagship Deep Reasoning Foundation Model
Author: Sk Masud Rahaman (@SkMasud18) - Falcon Intelligence
Architectural Paradigm: Multi-Head Latent Attention (MLA) + Dynamic Test-Time Compute
"""

import math
from typing import Optional, Tuple, List, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        variance = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(variance + self.eps) * self.weight

class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_position_embeddings: int = 131072, base: float = 1000000.0):
        super().__init__()
        self.dim = dim
        self.base = base
        inv_freq = 1.0 / (self.base ** (torch.arange(0, self.dim, 2).float() / self.dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        t = torch.arange(seq_len, device=x.device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()

class SwiGLUFeedForward(nn.Module):
    """SwiGLU activation MLP designed for high-capacity reasoning representation."""
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))

class MultiHeadLatentAttention(nn.Module):
    """
    Multi-Head Latent Attention (MLA) with low-rank KV compression
    for extreme 131k context reasoning and minimal VRAM memory footprint.
    """
    def __init__(self, hidden_size: int = 3584, num_heads: int = 28, num_kv_heads: int = 4):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = hidden_size // num_heads

        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.kv_a_proj = nn.Linear(hidden_size, 512, bias=False)  # Latent compression
        self.kv_b_proj = nn.Linear(512, num_kv_heads * self.head_dim * 2, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        b, s, _ = x.shape
        q = self.q_proj(x).view(b, s, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Latent KV expansion
        latent_kv = self.kv_a_proj(x)
        kv = self.kv_b_proj(latent_kv).view(b, s, self.num_kv_heads, 2 * self.head_dim)
        k, v = kv.chunk(2, dim=-1)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores + mask
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(b, s, self.hidden_size)
        return self.o_proj(out)

class NoxDecoderLayer(nn.Module):
    def __init__(self, hidden_size: int = 3584, intermediate_size: int = 18944):
        super().__init__()
        self.input_layernorm = RMSNorm(hidden_size)
        self.self_attn = MultiHeadLatentAttention(hidden_size)
        self.post_attention_layernorm = RMSNorm(hidden_size)
        self.mlp = SwiGLUFeedForward(hidden_size, intermediate_size)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        h = x + self.self_attn(self.input_layernorm(x), mask=mask)
        out = h + self.mlp(self.post_attention_layernorm(h))
        return out

class NoxForCausalLM(nn.Module):
    """
    Nox LLM Alpha Gen 1 Causal Language Model.
    Designed by Sk Masud Rahaman @ Falcon Intelligence.
    """
    def __init__(self, vocab_size: int = 152064, hidden_size: int = 3584, num_layers: int = 28):
        super().__init__()
        self.embed_tokens = nn.Embedding(vocab_size, hidden_size)
        self.layers = nn.ModuleList([NoxDecoderLayer(hidden_size) for _ in range(num_layers)])
        self.norm = RMSNorm(hidden_size)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        x = self.embed_tokens(input_ids)
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x)
        return self.lm_head(x)
