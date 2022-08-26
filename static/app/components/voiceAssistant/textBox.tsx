/* eslint-disable no-console */
import React from 'react';
import styled from '@emotion/styled';

import {NotifyStyle} from './voicePanel';

interface VoiceAssistantTextboxProps {
  notifyStyle?: NotifyStyle;
  resultText?: string;
  textBoxVisible?: boolean;
}

function getColorStyle(notifyStyle: NotifyStyle | undefined): string {
  switch (notifyStyle) {
    case NotifyStyle.Error:
      return `border-color: rgba(245, 84, 89, 0.5);
              background: #fccccd;`;
    case NotifyStyle.RecognizedResult:
      return `border-color: rgba(60, 116, 221, 0.5);
              background: #c5d6f5;`;
    case NotifyStyle.UnrecognizedResult:
      return `border-color: rgba(245, 176, 0, 0.5);
              background: #fef9ed;`;
    default:
      return '';
  }
}

const StyledWrapper = styled('div')<VoiceAssistantTextboxProps>`
  position: fixed;
  bottom: 2.5em;
  right: 3.5em;
  height: 50px;
  max-height: 50px;
  padding: 0.6em;
  padding-right: 3em;
  font-size: 18px;
  border-radius: 12px;
  border: 1px solid;
  box-shadow: 1px 1px 3px rgb(0 0 0 / 33%);
  opacity: 0;
  ${props => getColorStyle(props.notifyStyle)};
  transition: opacity 0.2s;

  &.voice-panel-visible {
    opacity: 1;
  }
`;

export class VoiceAssistantTextbox extends React.Component<
  VoiceAssistantTextboxProps,
  {}
> {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <StyledWrapper
        className={this.props.textBoxVisible ? 'voice-panel-visible' : ''}
        {...this.props}
      >
        {this.props.resultText}
      </StyledWrapper>
    );
  }
}
