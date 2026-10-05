const comment_open = "<comment>\n";
const comment_close = "\n<comment/>";

export function fork_comment(situation_id: string): string {
  return `Fork the causal chain from situation ID: ${situation_id}`;
}

export function split_leading_comment(text: string): { comment: string | null; rest: string } {
  if (!text.startsWith(comment_open)) {
    return { comment: null, rest: text };
  }
  const close_at = text.indexOf(comment_close);
  if (close_at < comment_open.length) {
    return { comment: null, rest: text };
  }
  const comment = text.slice(comment_open.length, close_at);
  let rest = text.slice(close_at + comment_close.length);
  if (rest.startsWith("\n")) {
    rest = rest.slice(1);
  }
  return { comment, rest };
}

export function join_comment(comment: string | null, rest: string): string {
  if (comment === null) {
    return rest;
  }
  const block = `${comment_open}${comment}${comment_close}`;
  if (rest === "") {
    return block;
  }
  return `${block}\n${rest}`;
}

export function prepend_fork_comment(text: string, situation_id: string): string {
  const { rest } = split_leading_comment(text);
  return join_comment(fork_comment(situation_id), rest);
}
