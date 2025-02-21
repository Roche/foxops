import styled from '@emotion/styled'

export const TableContainer = styled.div`
  position: relative;
  width: 100%;
  overflow: hidden;
  height: 100%;
  .table {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    .column-actions {
      margin-left: -1px;
      border-left: 1px solid ${x => x.theme.colors.grey};
    }
  }
  .sort-icon:not(.sorted) {
    opacity: 0;
  }
  .thead {
    position: sticky;
    top: 0;
    z-index: 1;



  }
  .tbody-scroll-box {
    position: relative;
    overflow: scroll;
    border-radius: .5rem .5rem 0 0; 

  }

  .tbody {
    display: flex;
    flex-direction: column;
    width: 100%;
    border-radius: 0 0 .5rem .5rem; 
    
    .tr > div:not(:last-child) {
      border-right: 1px solid ${x => x.theme.colors.grey};
    }
    .tr > div:last-child {
      position: sticky;
      right: 0;
    }


    .tr {
      border-bottom: 1px solid ${x => x.theme.colors.grey};
    }

    .tr:nth-of-type(even) {
      background-color: ${x => x.theme.colors.asideBg};

      .column-actions {
        background-color:  ${x => x.theme.colors.asideBg};
      }
    }

    .tr:nth-of-type(odd) {
      background-color: var(--base-bg);

      .column-actions {
        background-color: var(--base-bg);
      }
    }
  }
  .tr {
  display: flex;
  flex-grow: 1;
  flex-shrink: 0;
  min-width: 100%;
  width: fit-content;
  background-color:  ${x => x.theme.colors.asideBg};
  }

  .column-actions {
    background-color:  ${x => x.theme.colors.asideBg};
  }

  .column-actions > div{
    justify-content: flex-end;
  }

  .th {
    position: relative;
    line-height: 24px;
    white-space: nowrap;
    user-select: none;
    text-align: left;
    width: 200px;
    font-weight: 500;
    overflow: hidden;
    &:hover .sort-icon {
      opacity: 1;
    }

  }
  .th:not(:last-child) {
    border-right: 1px solid ${x => x.theme.colors.grey};
  }
  .th:last-child {
    width: 100%;
    position: sticky;
    right: 0;

  }
  .th-text {
    width: calc(100% - 32px);
    flex-shrink: 1;
    overflow: hidden;
    span {
      vertical-align: middle;
      display: inline-block;
      width: 100%;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .column-actions{
    width: 100% !important;
    max-width: 100% !important;
  }
  .td {
    font-size: 14px;
    display: flex;
    align-items: center;
    span {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .text-right {
    text-align: right;
    justify-content: flex-end;
  }
  .column-actions {
    .th-text {
      width: fit-content;
    }
  }
  .column-id {
    .th-text {
      width: fit-content;
    }
  }
  .td, .th {
    padding: 8px 16px;
    height: 48px;
    &.compact {
      padding: 2px 8px;
      height: 36px;
    }
  }
`
