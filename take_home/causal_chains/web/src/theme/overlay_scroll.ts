const HIDE_MS = 800;
const MIN_THUMB = 28;
const INSET = 3;

const thumbs = new WeakMap<HTMLElement, HTMLDivElement>();
const timers = new WeakMap<HTMLElement, number>();

export function overlay_thumb_box(
  scroll_top: number,
  scroll_height: number,
  client_height: number,
  track_top: number,
  track_height: number,
): { top: number; height: number } | null {
  const overflow = scroll_height - client_height;
  if (overflow <= 1 || track_height <= 0) {
    return null;
  }
  const height = Math.max(MIN_THUMB, Math.min(track_height, (client_height / scroll_height) * track_height));
  const travel = Math.max(0, track_height - height);
  const top = track_top + (scroll_top / overflow) * travel;
  return { top, height };
}

function place(node: HTMLElement, thumb: HTMLDivElement): boolean {
  const box = overlay_thumb_box(
    node.scrollTop,
    node.scrollHeight,
    node.clientHeight,
    0,
    node.clientHeight,
  );
  if (box === null) {
    thumb.classList.remove("is-on");
    return false;
  }
  thumb.style.height = `${box.height}px`;
  thumb.style.top = `${node.scrollTop + box.top}px`;
  thumb.style.right = "auto";
  const thumb_width = thumb.offsetWidth || 5;
  thumb.style.left = `${node.scrollLeft + node.clientWidth - thumb_width - INSET}px`;
  return true;
}

function thumb_for(node: HTMLElement): HTMLDivElement {
  const existing = thumbs.get(node);
  if (existing !== undefined) {
    return existing;
  }
  const thumb = document.createElement("div");
  thumb.className = "overlay-scrollbar";
  thumb.setAttribute("aria-hidden", "true");
  node.appendChild(thumb);
  thumbs.set(node, thumb);
  return thumb;
}

export function reveal_overlay_scrollbar(node: HTMLElement): void {
  const thumb = thumb_for(node);
  if (!place(node, thumb)) {
    return;
  }
  thumb.classList.add("is-on");
  const previous = timers.get(node);
  if (previous !== undefined) {
    window.clearTimeout(previous);
  }
  timers.set(
    node,
    window.setTimeout(() => {
      thumb.classList.remove("is-on");
      timers.delete(node);
    }, HIDE_MS),
  );
}

export function bind_overlay_scroll(node: HTMLElement): () => void {
  const on_scroll = () => reveal_overlay_scrollbar(node);
  node.addEventListener("scroll", on_scroll, { passive: true });
  return () => {
    node.removeEventListener("scroll", on_scroll);
    const pending = timers.get(node);
    if (pending !== undefined) {
      window.clearTimeout(pending);
    }
    timers.delete(node);
    thumbs.get(node)?.remove();
    thumbs.delete(node);
  };
}
