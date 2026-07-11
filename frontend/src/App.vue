<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <div class="app-shell">
    <aside class="sidebar" aria-label="主导航">
      <RouterLink class="brand" to="/documents" aria-label="RAG 文档审核首页">
        <span class="brand-mark" aria-hidden="true">RD</span>
        <span>
          <strong>Document Review</strong>
          <small>RAG LEGAL DESK</small>
        </span>
      </RouterLink>
      <nav class="nav-list">
        <RouterLink to="/documents"><span class="nav-index">01</span><span>文档列表</span></RouterLink>
        <RouterLink to="/upload"><span class="nav-index">02</span><span>上传文档</span></RouterLink>
      </nav>
      <div class="sidebar-foot"><span class="status-dot" aria-hidden="true"></span><span>Mock 审核环境</span></div>
    </aside>
    <main id="main-content" class="main-content" tabindex="-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in"><component :is="Component" /></Transition>
      </RouterView>
    </main>
  </div>
</template>
