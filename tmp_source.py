    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        doc_id: Optional[Union[str, List[str]]] = None,
        temperature: Optional[float] = None,
        stream_metadata: bool = False,
        enable_citations: bool = False
    ) -> Union[Dict[str, Any], Iterator[str], Iterator[Dict[str, Any]]]:
        """
        PageIndex Chat Completions. Optionally scoped to specific PageIndex documents.

        Args:
            messages (List[Dict[str, str]]): Conversation messages with 'role' and 'content' keys.
            stream (bool, optional): Enable streaming responses. Default is False.
            doc_id (Optional[Union[str, List[str]]], optional): Document ID(s) to scope the conversation. Can be a single ID or a list of IDs.
            temperature (Optional[float], optional): Sampling temperature. Default is None (uses API default).
            stream_metadata (bool, optional): If True and stream=True, return raw chunks with metadata instead of just text. Default is False.
            enable_citations (bool, optional): Enable citation instructions in responses. Default is False.

        Returns:
            Union[Dict[str, Any], Iterator[str], Iterator[Dict[str, Any]]]:
                - If stream=False: Complete response dictionary
                - If stream=True and stream_metadata=False: Iterator of text content chunks
                - If stream=True and stream_metadata=True: Iterator of raw response chunks with metadata
        """
        payload = {
            "messages": messages,
            "stream": stream
        }

        if doc_id is not None:
            payload["doc_id"] = doc_id

        if temperature is not None:
            payload["temperature"] = temperature

        if enable_citations:
            payload["enable_citations"] = enable_citations

        response = requests.post(
            f"{self.BASE_URL}/chat/completions/",
            headers=self._headers(),
            json=payload,
            stream=stream
        )

        if response.status_code != 200:
            raise PageIndexAPIError(f"Failed to get chat completion: {response.text}")

        if stream:
            if stream_metadata:
                return self._stream_chat_response_raw(response)
            else:
                return self._stream_chat_response(response)
        else:
            return response.json()
